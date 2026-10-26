#define _POSIX_C_SOURCE 199309L
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#endif

int A1(long long n) {
    if (n < 2)
        return 0;
    for (long long i = 2; i < n; i++) {
        if (n % i == 0)
            return 0;
    }
    return 1;
}

int A2(long long n) {
    if (n < 2)
        return 0;
    for (long long i = 2; i <= n / 2; i++) {
        if (n % i == 0)
            return 0;
    }
    return 1;
}

int A3(long long n) {
    if (n < 2)
        return 0;
    for (long long i = 2; i <= n / i; i++) {
        if (n % i == 0)
            return 0;
    }
    return 1;
}

int A4(long long n) {
    if (n < 2)
        return 0;
    if (n == 2)
        return 1;
    if (n % 2 == 0)
        return 0;
    for (long long i = 3; i <= n / i; i += 2) {
        if (n % i == 0)
            return 0;
    }
    return 1;
}

#ifdef _WIN32
static double now(void) {
    LARGE_INTEGER freq, counter;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&counter);
    return (double)counter.QuadPart / (double)freq.QuadPart;
}
#else
static double now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec / 1e9;
}
#endif

static int count_digits(long long n) {
    int d = 0;
    while (n > 0) {
        d++;
        n /= 10;
    }
    return d;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s dataset.txt [slow_limit]\n", argv[0]);
        return 1;
    }

    FILE *f = fopen(argv[1], "r");
    if (!f) {
        perror("fopen");
        return 1;
    }

    long long slow_limit = (argc > 2) ? atoll(argv[2]) : 2000000000LL;

    int (*alg[4])(long long) = {A1, A2, A3, A4};
    double sum[4] = {0, 0, 0, 0};
    int cnt[4] = {0, 0, 0, 0};

    printf("n,digits,A1,A2,A3,A4,all_prime\n");

    long long n;
    while (fscanf(f, "%lld", &n) == 1) {
        double t[4];
        int all_prime = 1;

        for (int k = 0; k < 4; k++) {
            if (k < 2 && n > slow_limit) {
                t[k] = -1;
                continue;
            }
            double start = now();
            int r = alg[k](n);
            double end = now();
            t[k] = end - start;
            sum[k] += t[k];
            cnt[k]++;
            if (!r)
                all_prime = 0;
        }

        printf("%lld,%d", n, count_digits(n));
        for (int k = 0; k < 4; k++) {
            if (t[k] < 0)
                printf(",NA");
            else
                printf(",%.9f", t[k]);
        }
        printf(",%s\n", all_prime ? "yes" : "NO");
        fflush(stdout);
    }

    printf("AVERAGE,");
    for (int k = 0; k < 4; k++) {
        if (cnt[k] == 0)
            printf(",NA");
        else
            printf(",%.9f", sum[k] / cnt[k]);
    }
    printf(",\n");

    fclose(f);
    return 0;
}