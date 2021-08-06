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
