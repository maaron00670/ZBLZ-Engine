/*
 * ZBLZ Engine - Speedhack Library
 *
 * This library intercepts time-related system calls to modify game speed.
 * Supports real-time speed changes via config file.
 */

#define _GNU_SOURCE
#include <dlfcn.h>
#include <time.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <errno.h>

/* Speed multiplier - updated in real-time from config file */
static volatile double speed_multiplier = 1.0;
static int initialized = 0;
static char config_path[512] = {0};

/* Frame counter for throttled config checks */
static unsigned int frame_counter = 0;
static const unsigned int FRAMES_BETWEEN_CHECKS = 60;  /* Check config every ~60 calls */

/* Original function pointers */
static int (*real_clock_gettime)(clockid_t, struct timespec *) = NULL;
static int (*real_gettimeofday)(struct timeval *, void *) = NULL;
static unsigned int (*real_sleep)(unsigned int) = NULL;
static int (*real_nanosleep)(const struct timespec *, struct timespec *) = NULL;
static int (*real_usleep)(useconds_t) = NULL;

/* Mutex for thread-safe speed/time updates */
static pthread_mutex_t speed_mutex = PTHREAD_MUTEX_INITIALIZER;

/* Piecewise linear transform state for each clock */
typedef struct {
    int64_t real_base_ns;
    int64_t virtual_base_ns;
    int64_t last_output_ns;
} time_transform_t;

static time_transform_t realtime_transform = {0, 0, 0};
static time_transform_t monotonic_transform = {0, 0, 0};
static time_transform_t monotonic_raw_transform = {0, 0, 0};

/* Convert timespec to nanoseconds */
static inline int64_t timespec_to_ns(const struct timespec *ts) {
    return (int64_t)ts->tv_sec * 1000000000LL + ts->tv_nsec;
}

/* Convert nanoseconds to timespec */
static inline void ns_to_timespec(int64_t ns, struct timespec *ts) {
    ts->tv_sec = ns / 1000000000LL;
    ts->tv_nsec = ns % 1000000000LL;
    if (ts->tv_nsec < 0) {
        ts->tv_nsec += 1000000000LL;
        ts->tv_sec -= 1;
    }
}

/* Convert timeval to microseconds */
static inline int64_t timeval_to_us(const struct timeval *tv) {
    return (int64_t)tv->tv_sec * 1000000LL + tv->tv_usec;
}

/* Convert microseconds to timeval */
static inline void us_to_timeval(int64_t us, struct timeval *tv) {
    tv->tv_sec = us / 1000000LL;
    tv->tv_usec = us % 1000000LL;
    if (tv->tv_usec < 0) {
        tv->tv_usec += 1000000LL;
        tv->tv_sec -= 1;
    }
}

/* Create config directory if needed */
static void ensure_config_dir(void) {
    char dir_path[256];
    snprintf(dir_path, sizeof(dir_path), "%s/.config/zblz", getenv("HOME") ? getenv("HOME") : "/tmp");
    mkdir(dir_path, 0755);
}

/* Read a raw clock using the original libc symbol */
static int read_real_clock_ns(clockid_t clk_id, int64_t *out_ns) {
    if (!real_clock_gettime || !out_ns) {
        return -1;
    }

    struct timespec ts;
    if (real_clock_gettime(clk_id, &ts) != 0) {
        return -1;
    }

    *out_ns = timespec_to_ns(&ts);
    return 0;
}

/* Initialize transform with identity mapping at the current real time */
static void init_transform(time_transform_t *transform, int64_t now_real_ns) {
    transform->real_base_ns = now_real_ns;
    transform->virtual_base_ns = now_real_ns;
    transform->last_output_ns = now_real_ns;
}

/* Apply transform for a specific clock, preserving monotonic outputs */
static int64_t apply_transform_locked(time_transform_t *transform, int64_t real_now_ns) {
    int64_t elapsed_real_ns = real_now_ns - transform->real_base_ns;
    int64_t virtual_now_ns = transform->virtual_base_ns + (int64_t)((double)elapsed_real_ns * speed_multiplier);

    /* Never move backwards from what we already returned */
    if (virtual_now_ns < transform->last_output_ns) {
        virtual_now_ns = transform->last_output_ns;
    }

    transform->last_output_ns = virtual_now_ns;
    return virtual_now_ns;
}

/* Re-anchor transform when speed changes to keep continuity */
static void reanchor_transform_locked(time_transform_t *transform, int64_t now_real_ns, double old_speed) {
    int64_t elapsed_real_ns = now_real_ns - transform->real_base_ns;
    int64_t virtual_now_ns = transform->virtual_base_ns + (int64_t)((double)elapsed_real_ns * old_speed);

    if (virtual_now_ns < transform->last_output_ns) {
        virtual_now_ns = transform->last_output_ns;
    }

    transform->real_base_ns = now_real_ns;
    transform->virtual_base_ns = virtual_now_ns;
    transform->last_output_ns = virtual_now_ns;
}

/* Re-anchor all transforms for a speed transition */
static void reanchor_all_transforms_locked(double old_speed) {
    int64_t now_rt_ns;
    int64_t now_mono_ns;
    int64_t now_raw_ns;

    if (read_real_clock_ns(CLOCK_REALTIME, &now_rt_ns) == 0) {
        reanchor_transform_locked(&realtime_transform, now_rt_ns, old_speed);
    }

    if (read_real_clock_ns(CLOCK_MONOTONIC, &now_mono_ns) == 0) {
        reanchor_transform_locked(&monotonic_transform, now_mono_ns, old_speed);
    }

#ifdef CLOCK_MONOTONIC_RAW
    if (read_real_clock_ns(CLOCK_MONOTONIC_RAW, &now_raw_ns) == 0) {
        reanchor_transform_locked(&monotonic_raw_transform, now_raw_ns, old_speed);
    }
#endif
}

/* Internal speed update with continuity guarantees */
static void update_speed_internal(double new_speed, int log_change) {
    if (new_speed <= 0.0 || new_speed > 100.0) {
        return;
    }

    pthread_mutex_lock(&speed_mutex);

    double old_speed = speed_multiplier;
    if (new_speed != old_speed) {
        reanchor_all_transforms_locked(old_speed);
        speed_multiplier = new_speed;

        if (log_change) {
            fprintf(stderr, "[ZBLZ] Speed changed to: %.2fx\n", speed_multiplier);
        }
    }

    pthread_mutex_unlock(&speed_mutex);
}

/* Setup config file path */
static void setup_config_path(void) {
    const char *home = getenv("HOME");
    if (!home) home = "/tmp";

    /* Use process PID or ZBLZ_PID environment variable */
    const char *zblz_pid = getenv("ZBLZ_PID");
    pid_t pid = zblz_pid ? (pid_t)atoi(zblz_pid) : getpid();

    snprintf(config_path, sizeof(config_path), "%s/.config/zblz/speed_%d.conf", home, pid);

    ensure_config_dir();

    /* Write initial speed to config */
    FILE *f = fopen(config_path, "w");
    if (f) {
        fprintf(f, "%.4f\n", speed_multiplier);
        fclose(f);
    }
}

/* Read speed from config file (called periodically) */
static void read_config(void) {
    FILE *f = fopen(config_path, "r");
    if (!f) {
        return;
    }

    double new_speed;
    if (fscanf(f, "%lf", &new_speed) == 1) {
        update_speed_internal(new_speed, 1);
    }

    fclose(f);
}

/* Check config file for updates (throttled) */
static inline void check_config_update(void) {
    frame_counter++;
    if (frame_counter >= FRAMES_BETWEEN_CHECKS) {
        frame_counter = 0;
        read_config();
    }
}

/* Get current speed (thread-safe) */
static inline double get_speed(void) {
    pthread_mutex_lock(&speed_mutex);
    double s = speed_multiplier;
    pthread_mutex_unlock(&speed_mutex);
    return s;
}

/* Initialize the library */
__attribute__((constructor))
static void init(void) {
    if (initialized) return;

    /* Load original functions */
    real_clock_gettime = dlsym(RTLD_NEXT, "clock_gettime");
    real_gettimeofday = dlsym(RTLD_NEXT, "gettimeofday");
    real_sleep = dlsym(RTLD_NEXT, "sleep");
    real_nanosleep = dlsym(RTLD_NEXT, "nanosleep");
    real_usleep = dlsym(RTLD_NEXT, "usleep");

    /* Get initial speed from environment */
    const char *speed_env = getenv("SPEED");
    if (speed_env != NULL) {
        double env_speed = atof(speed_env);
        if (env_speed > 0.0 && env_speed <= 100.0) {
            speed_multiplier = env_speed;
        }
    }

    /* Initialize identity transforms at current real time */
    int64_t now_rt_ns;
    int64_t now_mono_ns;

    if (read_real_clock_ns(CLOCK_REALTIME, &now_rt_ns) == 0) {
        init_transform(&realtime_transform, now_rt_ns);
    }

    if (read_real_clock_ns(CLOCK_MONOTONIC, &now_mono_ns) == 0) {
        init_transform(&monotonic_transform, now_mono_ns);
        monotonic_raw_transform = monotonic_transform;
    }

#ifdef CLOCK_MONOTONIC_RAW
    int64_t now_raw_ns;
    if (read_real_clock_ns(CLOCK_MONOTONIC_RAW, &now_raw_ns) == 0) {
        init_transform(&monotonic_raw_transform, now_raw_ns);
    }
#endif

    setup_config_path();

    initialized = 1;

    fprintf(stderr, "[ZBLZ Speedhack] Initialized\n");
    fprintf(stderr, "[ZBLZ Speedhack] Speed: %.2fx\n", speed_multiplier);
    fprintf(stderr, "[ZBLZ Speedhack] Config: %s\n", config_path);
    fprintf(stderr, "[ZBLZ Speedhack] PID: %d\n", getpid());
}

/* Cleanup on unload */
__attribute__((destructor))
static void cleanup(void) {
    /* Remove config file on exit */
    if (config_path[0] != '\0') {
        unlink(config_path);
    }
}

/*
 * Hooked clock_gettime
 */
int clock_gettime(clockid_t clk_id, struct timespec *tp) {
    if (!real_clock_gettime) {
        real_clock_gettime = dlsym(RTLD_NEXT, "clock_gettime");
    }

    int result = real_clock_gettime(clk_id, tp);
    if (result != 0 || tp == NULL) {
        return result;
    }

    check_config_update();

    if (clk_id == CLOCK_REALTIME || clk_id == CLOCK_MONOTONIC
#ifdef CLOCK_MONOTONIC_RAW
        || clk_id == CLOCK_MONOTONIC_RAW
#endif
    ) {
        int64_t current_ns = timespec_to_ns(tp);
        int64_t modified_ns = current_ns;

        pthread_mutex_lock(&speed_mutex);

        if (clk_id == CLOCK_REALTIME) {
            modified_ns = apply_transform_locked(&realtime_transform, current_ns);
        } else if (clk_id == CLOCK_MONOTONIC) {
            modified_ns = apply_transform_locked(&monotonic_transform, current_ns);
#ifdef CLOCK_MONOTONIC_RAW
        } else if (clk_id == CLOCK_MONOTONIC_RAW) {
            modified_ns = apply_transform_locked(&monotonic_raw_transform, current_ns);
#endif
        }

        pthread_mutex_unlock(&speed_mutex);

        ns_to_timespec(modified_ns, tp);
    }

    return 0;
}

/*
 * Hooked gettimeofday
 */
int gettimeofday(struct timeval *tv, void *tz) {
    if (!real_gettimeofday) {
        real_gettimeofday = dlsym(RTLD_NEXT, "gettimeofday");
    }

    int result = real_gettimeofday(tv, tz);
    if (result != 0 || tv == NULL) {
        return result;
    }

    check_config_update();

    int64_t current_us = timeval_to_us(tv);
    int64_t current_ns = current_us * 1000LL;

    pthread_mutex_lock(&speed_mutex);
    int64_t modified_ns = apply_transform_locked(&realtime_transform, current_ns);
    pthread_mutex_unlock(&speed_mutex);

    int64_t modified_us = modified_ns / 1000LL;
    us_to_timeval(modified_us, tv);

    return 0;
}

/*
 * Hooked sleep
 *
 * Safety rule:
 * - speed > 1.0: reduce sleep (speeds up loops)
 * - speed <= 1.0: keep original sleep to avoid excessive stalling/crashes
 */
unsigned int sleep(unsigned int seconds) {
    if (!real_sleep) {
        real_sleep = dlsym(RTLD_NEXT, "sleep");
    }

    check_config_update();

    double speed = get_speed();
    if (speed <= 1.0) {
        return real_sleep(seconds);
    }

    unsigned int adjusted = (unsigned int)(seconds / speed);
    if (adjusted == 0 && seconds > 0) {
        adjusted = 1;
    }

    return real_sleep(adjusted);
}

/*
 * Hooked nanosleep
 */
int nanosleep(const struct timespec *req, struct timespec *rem) {
    if (!real_nanosleep) {
        real_nanosleep = dlsym(RTLD_NEXT, "nanosleep");
    }

    if (req == NULL) {
        return real_nanosleep(req, rem);
    }

    check_config_update();

    double speed = get_speed();
    if (speed <= 1.0) {
        return real_nanosleep(req, rem);
    }

    int64_t req_ns = timespec_to_ns(req);
    int64_t adjusted_ns = (int64_t)(req_ns / speed);
    if (adjusted_ns == 0 && req_ns > 0) {
        adjusted_ns = 1;
    }

    struct timespec adjusted_req;
    ns_to_timespec(adjusted_ns, &adjusted_req);

    return real_nanosleep(&adjusted_req, rem);
}

/*
 * Hooked usleep
 */
int usleep(useconds_t usec) {
    if (!real_usleep) {
        real_usleep = dlsym(RTLD_NEXT, "usleep");
    }

    check_config_update();

    double speed = get_speed();
    if (speed <= 1.0) {
        return real_usleep(usec);
    }

    useconds_t adjusted = (useconds_t)(usec / speed);
    if (adjusted == 0 && usec > 0) {
        adjusted = 1;
    }

    return real_usleep(adjusted);
}

/*
 * Public API: Set speed directly (can be called via dlsym)
 */
void zblz_set_speed(double speed) {
    if (speed > 0.0 && speed <= 100.0) {
        update_speed_internal(speed, 1);

        FILE *f = fopen(config_path, "w");
        if (f) {
            fprintf(f, "%.4f\n", speed);
            fclose(f);
        }
    }
}

/*
 * Public API: Get current speed
 */
double zblz_get_speed(void) {
    return get_speed();
}

/*
 * Public API: Get config file path
 */
const char* zblz_get_config_path(void) {
    return config_path;
}
