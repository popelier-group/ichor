import errno
import getpass
import os
import stat
import subprocess
import time
from pathlib import Path
from signal import SIGTERM
from typing import List, Tuple

from ichor_lib.common.str import decode

USER_READ = stat.S_IRUSR
USER_WRITE = stat.S_IWUSR
USER_EXECUTE = stat.S_IXUSR
GROUP_READ = stat.S_IRGRP
GROUP_WRITE = stat.S_IWGRP
GROUP_EXECUTE = stat.S_IXGRP
OTHER_READ = stat.S_IROTH
OTHER_WRITE = stat.S_IWOTH
OTHER_EXECUTE = stat.S_IXOTH


def permissions(path: Path) -> Tuple[bool, bool, bool]:
    return (
        os.access(path, os.R_OK),
        os.access(path, os.W_OK),
        os.access(path, os.X_OK),
    )


def set_permission(path: Path, permission: int):
    os.chmod(path, permission)


def run_cmd(cmd) -> Tuple[str, str]:
    """Run a command in the terminal. This is used to submit jobs through ICHOR  (e.g. via qsub on CSF3).

    :param cmd: command to run in terminal.
    """
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=os.environ
    )
    stdout, stderr = p.communicate()
    return decode(stdout), decode(stderr)


def input_with_prefill(prompt: str, prefill: str = "") -> str:
    """
    Use over the builtin `input` function when wanting to prefill the input with text e.g.

    ```python
    >>> input_with_prefill("ENTER YOUR ANSWER: ", "example answer here")
    ENTER YOUR ANSWER: example answer here
    ```

    The user can then choose to replace the prefill text or use what is already there

    This is currently used in the settings menu in ichor when editing variables so that the
    current value is already prefilled and the user can just edit it but is general purpose code
    so can be used anywhere (unless you're on windows as readline isn't available... just defaults to normal input)
    """
    try:
        # Readline only available on Unix
        import readline

        readline.set_startup_hook(lambda: readline.insert_text(str(prefill)))
        return input(prompt)
    except ImportError:
        return input(prompt)
    finally:
        try:
            import readline

            readline.set_startup_hook()
        except ImportError:
            pass


def current_user() -> str:
    return getpass.getuser()


def current_user_groups() -> List[str]:
    """Returns the list of user groups the current user is in"""
    try:
        import grp

        groups = []
        for g in os.getgroups():
            try:
                groups.append(grp.getgrgid(g).gr_name)
            except KeyError:
                pass
        return groups
    except ImportError:
        import warnings

        warnings.warn("Warning: Cannot import 'grp' on current machine")
        return []


def pid_exists(pid: int) -> bool:
    """Check whether pid exists in the current process table."""
    if pid == 0:
        # According to "man 2 kill" PID 0 has a special meaning:
        # it refers to <<every process in the process group of the
        # calling process>> so we don't want to go any further.
        # If we get here it means this UNIX platform *does* have
        # a process with id 0.
        return True
    try:
        os.kill(pid, 0)
    except OSError as err:
        if err.errno == errno.ESRCH:
            # ESRCH == No such process
            return False
        elif err.errno == errno.EPERM:
            # EPERM clearly means there's a process to deny access to
            return True
        else:
            # According to "man 2 kill" possible error values are
            # (EINVAL, EPERM, ESRCH) therefore we should never get
            # here. If we do let's be explicit in considering this
            # an error.
            raise err
    else:
        return True


def kill_pid(pid: int):
    try:
        while True:
            os.kill(pid, SIGTERM)
            time.sleep(0.1)
    except OSError as err:
        err = str(err)
        if err.find("No such process") > 0:
            return
        else:
            raise err
