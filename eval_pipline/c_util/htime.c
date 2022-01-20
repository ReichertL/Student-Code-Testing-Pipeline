/* Holger Doebler's <stephaho@informatik.hu-berlin.de> replacement for gnu time */

const char* helptext =
  "Usage: htime [OPTIONS] COMMAND [ARG]...\n"
  "Run COMMAND, then print system resource usage.\n"
  "\n"
  "  -f '%%S %%U %%M %%x %%e'   unconditionally required\n"
  "  -h,  --help           display this help and exit\n"
  "  -o FILE               write to FILE instead of STDERR\n"
  "\n"
  "Rationale:\n"
  "time has only centi-second resolution because it is based on times()\n"
  "This program here is based on getrusage().\n"
  "%%S and %%U are printed with microsecond resolution.\n"
  "%%e is printed with nanosecond resolution.\n"
  "This does not imply any upper bound on measurement uncertainties.\n"
  "\n"
  "Limitations:\n"
  "  -f '%%S %%U %%M %%x %%e' must be given explicitly, other format strings are not supported.\n"
  "  COMMAND must be an absolute or explicit relative path, i.e., must start with \"/\", or \"./\", or \"../\"\n"
  "  Other OPTIONS than those printed above are not implemented.\n"
  "\n"
  "\n"
  "Licence: Public domain\n";

#include <errno.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

extern char **environ;

/* char *const subprocess_argv[] = {SUBPROCESS_PATH, "status", NULL}; */
char *const * subprocess_argv = NULL;

int
main(int argc, char**argv)
{
  char* subprocess_path = NULL;
  pid_t child_pid;
  int wstatus;
  struct rusage r_usage;
  char* out_path = "";
  char* format = "";
  FILE* out_file = stderr;

  /* the data we want to measure
   *   struct timeval ru_stime;  %S     Total number of CPU-seconds that the process spent in kernel mode.
   *   struct timeval ru_utime;  %U     Total number of CPU-seconds that the process spent in user mode.
   *   long   ru_maxrss;         %M     Maximum resident set size of the process during its lifetime, in Kbytes.
   *   %x     (Not in tcsh(1).)  Exit status of the command.
   *   %e     (Not in tcsh(1).)  Elapsed real time (in seconds).
   */
  struct timespec ts_start;
  struct timespec ts_end;
  double fmt_S;
  double fmt_U;
  int fmt_x;
  double fmt_e;

  /* parse argv */
  for (int i=1; i<argc; ++i) {
    if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
      fprintf(stdout, helptext);
      return 0;
    }
    if (strcmp(argv[i], "-o") == 0) {
      i ++;
      if (argc > i) {
        out_path = argv[i];
        continue;
      } else {
        return 125;
      }
    }
    if (strcmp(argv[i], "-f") == 0) {
      i ++;
      if (argc > i) {
        format = argv[i];
        continue;
      } else {
        return 125;
      }
    }
    if (argv[i] == NULL) {
      fprintf(stderr, "htime: missing program to run");
      return 125;
    }
    subprocess_path = argv[i];
    if (!(strncmp(subprocess_path, "/", 1) == 0 ||
          strncmp(subprocess_path, "./", 2) == 0 ||
          strncmp(subprocess_path, "../", 3) == 0)) {
      fprintf(stderr, "htime: subprocess path must be either absolute or explicitly relative; $PATH lookup is not supported.\n");
      return 125;
    }
    subprocess_argv = argv + i;
    break;
  }
  /* check argv */
  if (strcmp("%S %U %M %x %e", format) != 0) {
    fprintf(stderr, "ERROR: bad format string. Use '%%S %%U %%M %%x %%e'\n");
    return 125;
  }
  /* start the stop watch */
  if (clock_gettime(CLOCK_REALTIME, &ts_start) != 0) {
    fprintf(stderr, "clock error\n");
    return 125;
  }
  /* fork */
  if ((child_pid = fork()) == 0) { /* If we are the child, just substitue ourselves with execve() */
    execve(subprocess_path, subprocess_argv, environ);
    return 127; /* FIXME: 127 is "so such file or directory"; we always return this if execve fails; we should do it better! */
  } else { /* OK, we are the parent */
    wait(&wstatus); /* wait for the child to terminate */
    /* stop the stopwatch */
    if (clock_gettime(CLOCK_REALTIME, &ts_end) != 0) {
      fprintf(stderr, "clock error\n");
      return 125;
    }
    /* retrieve exitstatus */
    if (WIFEXITED(wstatus)) {
      fmt_x = WEXITSTATUS(wstatus);
    } else {
      fmt_x = -1;
    }
    getrusage(RUSAGE_CHILDREN, &r_usage);
    /* calculate realtime */
    fmt_e = 1e-9 * (1e9 * (ts_end.tv_sec - ts_start.tv_sec) + 1.0 * ts_end.tv_nsec - 1.0 * ts_start.tv_nsec);
    /* calculate system cpu time */
    fmt_S = r_usage.ru_stime.tv_sec + 1e-6 * r_usage.ru_stime.tv_usec;
    /* calculate user cpu time */
    fmt_U = r_usage.ru_utime.tv_sec + 1e-6 * r_usage.ru_utime.tv_usec;
    /* try to open out_path */
    if (out_path[0] != 0) {
      out_file = fopen(out_path, "w");
      if (out_file == NULL)
        return 125;
    }
    /* actually write '%S %U %M %x %e' */
    fprintf(out_file, "%.6f %.6f %ld %d %.9f\n", fmt_S, fmt_U, r_usage.ru_maxrss, fmt_x, fmt_e);
    /* close out_file if needed */
    if (out_file != stderr)
      fclose(out_file);
  }
  return fmt_x;
}
