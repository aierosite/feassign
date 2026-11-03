#define _POSIX_C_SOURCE 200809L
#include <signal.h>
#include <stdint.h>
#include <stdio.h>

static int stdout_failed;
static int stderr_failed;

int32_t fa_io_init(void) {
    struct sigaction action = {0};
    action.sa_handler = SIG_IGN;
    if (sigemptyset(&action.sa_mask) != 0 ||
        sigaction(SIGPIPE, &action, NULL) != 0) return -1;
    return 0;
}

int32_t fa_read_char(void) {
    int byte = fgetc(stdin);
    if (byte != EOF) return (int32_t)(unsigned char)byte;
    if (ferror(stdin)) return -2;
    return feof(stdin) ? -1 : -2;
}

int32_t fa_write_char(int32_t byte, int32_t stream) {
    if (byte < 0 || byte > 255 || (stream != 0 && stream != 1)) return -1;
    int *failed = stream == 0 ? &stdout_failed : &stderr_failed;
    FILE *destination = stream == 0 ? stdout : stderr;
    if (*failed) return -1;
    if (fputc((unsigned char)byte, destination) == EOF) {
        *failed = 1;
        return -1;
    }
    return 0;
}

int32_t fa_io_finish(void) {
    int out = fflush(stdout);
    int err = fflush(stderr);
    return stdout_failed || stderr_failed || out == EOF || err == EOF ||
           ferror(stdout) || ferror(stderr) ? -1 : 0;
}
