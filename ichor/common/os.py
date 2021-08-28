import os
import subprocess
from typing import Tuple, List

from ichor.common.str import decode


def run_cmd(cmd: List[str]) -> Tuple[str, str]:
    """ Run a command in the terminal. This is used to submit jobs through ICHOR  (e.g. via qsub on CSF3).
    
    :param cmd: command to run in terminal. 
    """
    print(cmd)
    p = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=os.environ
    )
    stdout, stderr = p.communicate()
    return decode(stdout), decode(stderr)
