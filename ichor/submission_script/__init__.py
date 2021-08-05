from pathlib import Path

from ichor.submission_script.aimall import AIMAllCommand
from ichor.submission_script.check_manager import (CheckManager, default_check,
                                                   print_completed)
from ichor.submission_script.data_lock import DataLock
from ichor.submission_script.ferebus import FerebusCommand
from ichor.submission_script.gaussian import GaussianCommand
from ichor.submission_script.ichor import ICHORCommand
from ichor.submission_script.python import PythonCommand
from ichor.submission_script.submision_script import SubmissionScript
from ichor.submission_script.timing_manager import TimingManager


def prepend_script_directory(paths):
    from ichor.globals import GLOBALS

    for key, val in paths.items():
        if isinstance(val, dict):
            paths[key] = prepend_script_directory(paths)
        else:
            paths[key] = GLOBALS.FILE_STRUCTURE["scripts"] / val
    return paths


class ScriptNames(dict):
    """A helper class which retruns the full path of a particular script that is used to submit job files
    for programs like Guassian and AIMALL. These jobs are submitted to compute nodes on CSF3/FFLUXLAB."""

    def __getitem__(self, item: str):
        """
        :param item: a key which corresponds to a particular script file. See SCRIPT_NAMES.
        """
        from ichor.globals import GLOBALS  # import globals as the paths to the script directory is defined there

        script = super().__getitem__(item)  # call dict __getitem__ method to get the script name (the value corresponding to the given key)
        if isinstance(script, (str, Path)):
            return GLOBALS.FILE_STRUCTURE["scripts"] / script  # append the script name to the path where the scripts are located
        else:
            return script


SCRIPT_NAMES = ScriptNames(
    {
        "gaussian": "GAUSSIAN.sh",
        "aimall": "AIMALL.sh",
        "ferebus": "FEREBUS.sh",
        "ichor": ScriptNames(
            {
                "gaussian": "ICHOR_GAUSSIAN.sh",
                "aimall": "ICHOR_AIMALL.sh",
                "ferebus": "ICHOR_FEREBUS.sh",
                "adaptive_sampling": "ICHOR_ADAPTIVE_SAMPLING.sh",
                "make_sets": "ICHOR_MAKE_SETS.sh"
            }
        ),
    }
)

__all__ = [
    "SubmissionScript",
    "GaussianCommand",
    "AIMAllCommand",
    "FerebusCommand",
    "PythonCommand",
    "ICHORCommand",
    "DataLock",
    "TimingManager",
    "SCRIPT_NAMES",
    "CheckManager",
    "print_completed",
    "default_check",
]
