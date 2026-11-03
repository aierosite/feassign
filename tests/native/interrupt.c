/* Test-only preload: give the real blocking read a handled, non-restarted signal.
 * The production CLI changes SIGPIPE only; no test handler is shipped in it. */
#define _POSIX_C_SOURCE 200809L
#include <signal.h>
#include <unistd.h>

static void interrupted(int signal_number) { (void)signal_number; }

__attribute__((constructor)) static void prepare_interrupt(void) {
    struct sigaction action = {0};
    action.sa_handler = interrupted;
    if (sigemptyset(&action.sa_mask) != 0 ||
        sigaction(SIGUSR1, &action, NULL) != 0) _exit(120);
}
