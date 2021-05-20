from ichor.submission_script.aimall import AIMAllCommand
from ichor.submission_script.ferebus import FerebusCommand
from ichor.submission_script.gaussian import GaussianCommand
from ichor.submission_script.ichor import ICHORCommand
from ichor.submission_script.python import PythonCommand
from ichor.submission_script.submision_script import SubmissionScript


def prepend_script_directory(paths):
    from ichor.globals import GLOBALS

    for key, val in paths.items():
        if isinstance(val, dict):
            paths[key] = prepend_script_directory(paths)
        else:
            paths[key] = GLOBALS.FILE_STRUCTURE["scripts"] / val
    return paths


SCRIPT_NAMES = prepend_script_directory(
    {
        "gaussian": "GAUSSIAN.sh",
        "aimall": "AIMALL.sh",
        "ferebus": "FEREBUS.sh",
        "ichor": {
            "gaussian": "ICHOR_GAUSSIAN.sh",
            "aimall": "ICHOR_AIMALL.sh",
            "ferebus": "ICHOR_FEREBUS.sh",
            "adaptive_sampling": "ICHOR_ADAPTIVE_SAMPLING.sh",
        },
    }
)

__all__ = [
    "SubmissionScript",
    "GaussianCommand",
    "AIMAllCommand",
    "FerebusCommand",
    "PythonCommand",
    "ICHORCommand",
    "SCRIPT_NAMES",
]
