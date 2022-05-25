""" Used to run ICHOR as a deamon, where it is detached from terminal."""

import atexit
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path

from ichor.ichor_lib.common.io import mkdir, remove
from ichor.ichor_lib.common.os import kill_pid, pid_exists
from ichor.ichor_hpc import FILE_STRUCTURE


class DaemonRunning(Exception):
    pass


class Daemon(ABC):
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method

    Credit: Sander Marechal (https://bit.ly/3frF5RK)
    """

    def __init__(
        self,
        pidfile: Path,
        stdin: Path = Path("/dev/null"),
        stdout: Path = Path("/dev/null"),
        stderr: Path = Path("/dev/null"),
    ):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

        mkdir(pidfile.parent)
        mkdir(stdin.parent)
        mkdir(stdout.parent)
        mkdir(stderr.parent)

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(
                "fork #1 failed: %d (%s)\n" % (e.errno, e.strerror)
            )
            sys.exit(1)

        # decouple from parent environment
        cwd = os.getcwd()
        os.chdir("/")
        os.setsid()
        os.umask(0)
        os.chdir(cwd)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(
                "fork #2 failed: %d (%s)\n" % (e.errno, e.strerror)
            )
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        # si = open(self.stdin, "r")
        so = open(self.stdout, "a+")
        se = open(self.stderr, "a+")
        # os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        with open(self.pidfile, "w+") as pf:
            pf.write(f"{pid}\n")
        with open(FILE_STRUCTURE["pids"], "a") as f:
            f.write(f"{pid}\n")

    def delpid(self):
        if os.path.exists(self.pidfile):
            remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        if self.pidfile.exists():
            with open(self.pidfile, "r") as f:
                if pid_exists(int(f.read().strip())):
                    raise DaemonRunning(
                        f"Error: Daemon Running (pid file: {self.pidfile})"
                    )

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        if not self.pidfile.exists():
            return

        with open(self.pidfile, "r") as f:
            pid = int(f.read().strip())

        if not pid_exists(pid):
            return

        # Try killing the daemon process
        kill_pid(pid)
        self.delpid()

    def check(self) -> bool:
        if not self.pidfile.exists():
            return False
        with open(self.pidfile, "r") as f:
            pid = int(f.read().strip())
        return pid_exists(pid)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    @abstractmethod
    def run(self):
        pass
