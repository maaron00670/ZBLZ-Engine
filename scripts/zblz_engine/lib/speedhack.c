/*
 * ZBLZ Engine - Speedhack Library
 * 
 * This library intercepts time-related system calls to modify game speed.
 * Supports real-time speed changes via config file.
 * 
 * Compile:
 *   gcc -shared -fPIC -o libspeedhack.so speedhack.c -ldl -lpthread
 * 
 * Usage:
 *   LD_PRELOAD=/path/to/libspeedhack.so ZBLZ_PID=$$ ./game
 * 
 * Real-time control:
 *   The library reads speed from ~/.config/zblz/speed_<PID>.conf
 *   ZBLZ Engine GUI writes to this file when speed changes
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
static time_t last_config_check = 0;
static const int CONFIG_CHECK_INTERVAL = 0;  /* Check every call (for responsiveness) */

/* Frame counter for throttled config checks */
static unsigned int frame_counter = 0;
static const unsigned int FRAMES_BETWEEN_CHECKS = 60;  /* Check config every ~60 frames */

/* Original timestamps at initialization */
static struct timespec init_realtime;
static struct timespec init_monotonic;
static struct timeval init_gettimeofday;

/* Original function pointers */
static int (*real_clock_gettime)(clockid_t, struct timespec *) = NULL;
static int (*real_gettimeofday)(struct timeval *, void *) = NULL;
static unsigned int (*real_sleep)(unsigned int) = NULL;
static int (*real_nanosleep)(const struct timespec *, struct timespec *) = NULL;
static int (*real_usleep)(useconds_t) = NULL;

/* Mutex for thread-safe speed updates */
static pthread_mutex_t speed_mutex = PTHREAD_MUTEX_INITIALIZER;

/* Create config directory if needed */
static void ensure_config_dir(void) {
    char dir_path[256];
    snprintf(dir_path, sizeof(dir_path), "%s/.config/zblz", getenv("HOME") ? getenv("HOME") : "/tmp");
    mkdir(dir_path, 0755);
}

/* Setup config file path */
static void setup_config_path(void) {
    const char *home = getenv("HOME");
    if (!home) home = "/tmp";
    
    /* Use process PID or ZBLZ_PID environment variable */
    const char *zblz_pid = getenv("ZBLZ_PID");
    pid_t pid = zblz_pid ? (pid_t)atoi(zblz_pid) : getpid();
    
    snprintf(config_path, sizeof(config_path), 
             "%s/.config/zblz/speed_%d.conf", home, pid);
    
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
    if (f) {
        double new_speed;
        if (fscanf(f, "%lf", &new_speed) == 1 && new_speed > 0.0 && new_speed <= 100.0) {
            pthread_mutex_lock(&speed_mutex);
            if (new_speed != speed_multiplier) {
                speed_multiplier = new_speed;
                fprintf(stderr, "[ZBLZ] Speed changed to: %.2fx\n", speed_multiplier);
            }
            pthread_mutex_unlock(&speed_mutex);
        }
        fclose(f);
    }
}

/* Check config file for updates (throttled) */
static inline void check_config_update(void) {
    frame_counter++;
    if (frame_counter >= FRAMES_BETWEEN_CHECKS) {
        frame_counter = 0;
        read_config();
    }
}

/* Initialize the library */
__attribute__((constructor))
static void init(void) {
    if (initialized) return;
    
    /* Get initial speed from environment */
    const char *speed_env = getenv("SPEED");
    if (speed_env != NULL) {
        speed_multiplier = atof(speed_env);
        if (speed_multiplier <= 0.0) {
            speed_multiplier = 1.0;
        }
    }
    
    /* Load original functions */
    real_clock_gettime = dlsym(RTLD_NEXT, "clock_gettime");
    real_gettimeofday = dlsym(RTLD_NEXT, "gettimeofday");
    real_sleep = dlsym(RTLD_NEXT, "sleep");
    real_nanosleep = dlsym(RTLD_NEXT, "nanosleep");
    real_usleep = dlsym(RTLD_NEXT, "usleep");
    
    /* Save initial timestamps */
    if (real_clock_gettime) {
        real_clock_gettime(CLOCK_REALTIME, &init_realtime);
        real_clock_gettime(CLOCK_MONOTONIC, &init_monotonic);
    }
    if (real_gettimeofday) {
        real_gettimeofday(&init_gettimeofday, NULL);
    }
    
    /* Setup config file for real-time control */
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

/* Get current speed (thread-safe) */
static inline double get_speed(void) {
    pthread_mutex_lock(&speed_mutex);
    double s = speed_multiplier;
    pthread_mutex_unlock(&speed_mutex);
    return s;
}

/* Convert timespec to nanoseconds */
static inline int64_t timespec_to_ns(const struct timespec *ts) {
    return (int64_t)ts->tv_sec * 1000000000LL + ts->tv_nsec;
}

/* Convert nanoseconds to timespec */
static inline void ns_to_timespec(int64_t ns, struct timespec *ts) {
    ts->tv_sec = ns / 1000000000LL;
    ts->tv_nsec = ns % 1000000000LL;
}

/* Convert timeval to microseconds */
static inline int64_t timeval_to_us(const struct timeval *tv) {
    return (int64_t)tv->tv_sec * 1000000LL + tv->tv_usec;
}

/* Convert microseconds to timeval */
static inline void us_to_timeval(int64_t us, struct timeval *tv) {
    tv->tv_sec = us / 1000000LL;
    tv->tv_usec = us % 1000000LL;
}

/* 
 * Hooked clock_gettime
 * Main function for time manipulation
 */
int clock_gettime(clockid_t clk_id, struct timespec *tp) {
    if (!real_clock_gettime) {
        real_clock_gettime = dlsym(RTLD_NEXT, "clock_gettime");
    }
    
    /* Check for config updates periodically */
    check_config_update();
    
    int result = real_clock_gettime(clk_id, tp);
    if (result != 0) return result;
    
    /* Only modify for game-relevant clocks */
    if (clk_id == CLOCK_REALTIME || 
        clk_id == CLOCK_MONOTONIC || 
        clk_id == CLOCK_MONOTONIC_RAW) {
        
        struct timespec *init_ts = (clk_id == CLOCK_REALTIME) 
                                    ? &init_realtime 
                                    : &init_monotonic;
        
        double speed = get_speed();
        
        /* Calculate elapsed time */
        int64_t current_ns = timespec_to_ns(tp);
        int64_t init_ns = timespec_to_ns(init_ts);
        int64_t elapsed_ns = current_ns - init_ns;
        
        /* Apply speed multiplier */
        int64_t modified_elapsed = (int64_t)(elapsed_ns * speed);
        int64_t modified_ns = init_ns + modified_elapsed;
        
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
    if (result != 0 || tv == NULL) return result;
    
    double speed = get_speed();
    
    /* Calculate elapsed time */
    int64_t current_us = timeval_to_us(tv);
    int64_t init_us = timeval_to_us(&init_gettimeofday);
    int64_t elapsed_us = current_us - init_us;
    
    /* Apply speed multiplier */
    int64_t modified_elapsed = (int64_t)(elapsed_us * speed);
    int64_t modified_us = init_us + modified_elapsed;
    
    us_to_timeval(modified_us, tv);
    
    return 0;
}

/*
 * Hooked sleep - adjust sleep duration
 */
unsigned int sleep(unsigned int seconds) {
    if (!real_sleep) {
        real_sleep = dlsym(RTLD_NEXT, "sleep");
    }
    
    double speed = get_speed();
    
    /* Adjust sleep time inversely to speed */
    unsigned int adjusted = (unsigned int)(seconds / speed);
    if (adjusted == 0 && seconds > 0) {
        adjusted = 1;  /* Minimum 1 second */
    }
    
    return real_sleep(adjusted);
}

/*
 * Hooked nanosleep - adjust sleep duration
 */
int nanosleep(const struct timespec *req, struct timespec *rem) {
    if (!real_nanosleep) {
        real_nanosleep = dlsym(RTLD_NEXT, "nanosleep");
    }
    
    if (req == NULL) {
        return real_nanosleep(req, rem);
    }
    
    double speed = get_speed();
    
    /* Adjust sleep time inversely to speed */
    int64_t req_ns = timespec_to_ns(req);
    int64_t adjusted_ns = (int64_t)(req_ns / speed);
    
    struct timespec adjusted_req;
    ns_to_timespec(adjusted_ns, &adjusted_req);
    
    return real_nanosleep(&adjusted_req, rem);
}

/*
 * Hooked usleep - adjust sleep duration
 */
int usleep(useconds_t usec) {
    if (!real_usleep) {
        real_usleep = dlsym(RTLD_NEXT, "usleep");
    }
    
    double speed = get_speed();
    
    /* Adjust sleep time inversely to speed */
    useconds_t adjusted = (useconds_t)(usec / speed);
    
    return real_usleep(adjusted);
}

/*
 * Public API: Set speed directly (can be called via dlsym)
 */
void zblz_set_speed(double speed) {
    if (speed > 0.0 && speed <= 100.0) {
        pthread_mutex_lock(&speed_mutex);
        speed_multiplier = speed;
        pthread_mutex_unlock(&speed_mutex);
        
        /* Also write to config file */
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
