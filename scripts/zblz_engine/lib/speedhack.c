/*
 * ZBLZ Engine - Speedhack Library
 * 
 * This library intercepts time-related system calls to modify game speed.
 * 
 * Compile:
 *   gcc -shared -fPIC -o libspeedhack.so speedhack.c -ldl
 * 
 * Usage:
 *   LD_PRELOAD=/path/to/libspeedhack.so SPEED=2.0 ./game
 * 
 * Environment Variables:
 *   SPEED - Speed multiplier (default: 1.0)
 *           Values > 1.0 = faster, Values < 1.0 = slower
 */

#define _GNU_SOURCE
#include <dlfcn.h>
#include <time.h>
#include <sys/time.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

/* Speed multiplier - set via SPEED environment variable */
static double speed_multiplier = 1.0;
static int initialized = 0;

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

/* Initialize the library */
__attribute__((constructor))
static void init(void) {
    if (initialized) return;
    
    /* Get speed multiplier from environment */
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
    
    initialized = 1;
    
    fprintf(stderr, "[ZBLZ Speedhack] Initialized with speed multiplier: %.2f\n", 
            speed_multiplier);
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
    
    int result = real_clock_gettime(clk_id, tp);
    if (result != 0) return result;
    
    /* Only modify for game-relevant clocks */
    if (clk_id == CLOCK_REALTIME || 
        clk_id == CLOCK_MONOTONIC || 
        clk_id == CLOCK_MONOTONIC_RAW) {
        
        struct timespec *init_ts = (clk_id == CLOCK_REALTIME) 
                                    ? &init_realtime 
                                    : &init_monotonic;
        
        /* Calculate elapsed time */
        int64_t current_ns = timespec_to_ns(tp);
        int64_t init_ns = timespec_to_ns(init_ts);
        int64_t elapsed_ns = current_ns - init_ns;
        
        /* Apply speed multiplier */
        int64_t modified_elapsed = (int64_t)(elapsed_ns * speed_multiplier);
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
    
    /* Calculate elapsed time */
    int64_t current_us = timeval_to_us(tv);
    int64_t init_us = timeval_to_us(&init_gettimeofday);
    int64_t elapsed_us = current_us - init_us;
    
    /* Apply speed multiplier */
    int64_t modified_elapsed = (int64_t)(elapsed_us * speed_multiplier);
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
    
    /* Adjust sleep time inversely to speed */
    unsigned int adjusted = (unsigned int)(seconds / speed_multiplier);
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
    
    /* Adjust sleep time inversely to speed */
    int64_t req_ns = timespec_to_ns(req);
    int64_t adjusted_ns = (int64_t)(req_ns / speed_multiplier);
    
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
    
    /* Adjust sleep time inversely to speed */
    useconds_t adjusted = (useconds_t)(usec / speed_multiplier);
    
    return real_usleep(adjusted);
}

/*
 * Allow changing speed at runtime via environment variable check
 * Call this function to refresh speed from SPEED env var
 */
void zblz_refresh_speed(void) {
    const char *speed_env = getenv("SPEED");
    if (speed_env != NULL) {
        double new_speed = atof(speed_env);
        if (new_speed > 0.0) {
            speed_multiplier = new_speed;
            fprintf(stderr, "[ZBLZ Speedhack] Speed updated to: %.2f\n", speed_multiplier);
        }
    }
}

/*
 * Get current speed multiplier
 */
double zblz_get_speed(void) {
    return speed_multiplier;
}

/*
 * Set speed multiplier directly
 */
void zblz_set_speed(double speed) {
    if (speed > 0.0) {
        speed_multiplier = speed;
    }
}
