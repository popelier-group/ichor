import os
import subprocess
from typing import List, Tuple

from ichor.common.str import decode


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


def current_user_groups() -> List[str]:
    """Returns the list of user groups the current user is in"""
    try:
        import grp

        return [grp.getgrgid(g).gr_name for g in os.getgroups()]
    except ImportError:
        import warnings

        warnings.warn("Warning: Cannot import 'grp' on current machine")
        return []
