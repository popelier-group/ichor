from pathlib import Path

from ichor.common.types import MutableValue
from ichor.file_structure import FILE_STRUCTURE
from ichor.submission_script.aimall_command import AIMAllCommand
from ichor.submission_script.amber_command import AmberCommand
from ichor.submission_script.check_manager import (CheckManager, default_check,
                                                   print_completed)
from ichor.submission_script.cp2k_command import CP2KCommand
from ichor.submission_script.data_lock import DataLock
from ichor.submission_script.dlpoly_command import DlpolyCommand
from ichor.submission_script.ferebus_command import FerebusCommand
from ichor.submission_script.gaussian_command import GaussianCommand
from ichor.submission_script.ichor_command import ICHORCommand
from ichor.submission_script.morfi_command import MorfiCommand
from ichor.submission_script.pandora_command import (PandoraCommand,
                                                     PandoraMorfiCommand,
                                                     PandoraPySCFCommand)
from ichor.submission_script.python_command import PythonCommand
from ichor.submission_script.script_timing_manager import TimingManager
from ichor.submission_script.submision_script import (SUBMIT_ON_COMPUTE,
                                                      SubmissionScript)
from ichor.submission_script.tyche_command import TycheCommand


def prepend_script_directory(paths):
    from ichor.file_structure import FILE_STRUCTURE

    for key, val in paths.items():
        if isinstance(val, dict):
            paths[key] = prepend_script_directory(paths)
        else:
            paths[key] = FILE_STRUCTURE["scripts"] / val
    return paths


class ScriptNames(dict):
    """A helper class which retruns the full path of a particular script that is used to submit job files
    for programs like Guassian and AIMALL. All the script files are stored into a directory GLOBALS.FILE_STRUCTURE["scripts"].
    These scripts are submitted to compute nodes on CSF3/FFLUXLAB which initiates a job."""

    parent: Path = MutableValue(FILE_STRUCTURE["scripts"])
    modify: str = MutableValue("")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getitem__(self, item):
        """
        :param item: a key which corresponds to a particular script file value. See SCRIPT_NAMES.
        """
        script = super().__getitem__(
            item
        )  # call dict __getitem__ method to get the script name (the value corresponding to the given key)
        # if an ichor script, you have to do SCRIPT_NAMES["ichor"]["gaussian"] as SCRIPT_NAMES["ichor"] retruns a ScriptNames type object
        # then the second time this object is indexed with ["gaussian"], it will be an instance of "str", so this if statement will be executed
        if isinstance(script, (str, Path)):
            # append the script name to the path where the scripts are located and modify script name with self.modify
            return self.parent.value / (script + self.modify.value)
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
                "active_learning": "ICHOR_ACTIVE_LEARNING.sh",
                "make_sets": "ICHOR_MAKE_SETS.sh",
                "collate_log": "ICHOR_COLLATE_LOG.sh",
                "dlpoly": ScriptNames(
                    {
                        "setup": "ICHOR_DLPOLY_SETUP.sh",
                        "gaussian": "ICHOR_DLPOLY_GAUSSIAN.sh",
                        "energies": "ICHOR_DLPOLY_ENERGIES.sh",
                    }
                ),
                "pandora": ScriptNames(
                    {
                        "pyscf": "ICHOR_PANDORA_PYSCF.sh",
                        "morfi": "ICHOR_PANDORA_MORFI.sh",
                    }
                ),
            }
        ),
        "pandora": ScriptNames(
            {"pyscf": "PANDORA_PYSCF.sh", "morfi": "PANDORA_MORFI.sh"}
        ),
        "dlpoly": "DLPOLY.sh",
        "dlpoly_gaussian": "ICHOR_DLPOLY_GAUSSIAN.sh",
        "amber": "AMBER.sh",
        "cp2k": "CP2K.sh",
        "opt": ScriptNames(
            {"gaussian": "GEOM_OPT.sh", "convert": "GEOM_OPT_CONVERT.sh"}
        ),
        "analysis": ScriptNames({"geometry": "GEOMETRY_ANALYSIS.sh"}),
    }
)

__all__ = [
    "SubmissionScript",
    "GaussianCommand",
    "AIMAllCommand",
    "FerebusCommand",
    "DlpolyCommand",
    "PythonCommand",
    "ICHORCommand",
    "DataLock",
    "TimingManager",
    "SCRIPT_NAMES",
    "CheckManager",
    "print_completed",
    "default_check",
    "PandoraCommand",
    "PandoraPySCFCommand",
    "PandoraMorfiCommand",
    "MorfiCommand",
    "AmberCommand",
    "CP2KCommand",
    "TycheCommand",
    "SUBMIT_ON_COMPUTE",
]
