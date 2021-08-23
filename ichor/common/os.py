import os
import subprocess
from typing import Tuple

from ichor.common.str import decode


def run_cmd(cmd) -> Tuple[str, str]:
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=os.environ
    )
    stdout, stderr = p.communicate()
    return decode(stdout), decode(stderr)


def input_with_prefill(prompt: str, prefill: str = "") -> str:
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
