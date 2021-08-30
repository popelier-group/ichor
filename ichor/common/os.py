import os
import subprocess
from typing import Tuple

from ichor.common.str import decode


def run_cmd(cmd) -> Tuple[str, str]:
    """ Run a command in the terminal. This is used to submit jobs through ICHOR  (e.g. via qsub on CSF3).
    
    :param cmd: command to run in terminal. 
    """
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=os.environ
    )
    stdout, stderr = p.communicate()
    return decode(stdout), decode(stderr)


def input_with_prefill(prompt: str, prefill: str = "") -> str:
    # matt_todo: Where is this function needed? Better to give examples here. Also good to explain the name because I can't tell what the function is going to do from it.
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
