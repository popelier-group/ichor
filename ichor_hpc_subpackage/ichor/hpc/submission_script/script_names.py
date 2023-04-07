from pathlib import Path

from ichor.core.common.types import MutableValue
from ichor.hpc import FILE_STRUCTURE


def prepend_script_directory(paths):
    from ichor.hpc import FILE_STRUCTURE

    for key, val in paths.items():
        if isinstance(val, dict):
            paths[key] = prepend_script_directory(paths)
        else:
            paths[key] = FILE_STRUCTURE["scripts"] / val
    return paths


class ScriptNames(dict):
    """A helper class which retruns the full path of a particular script that is used to submit job files
    for programs like Guassian and AIMALL. All the script files are stored into a directory FILE_STRUCTURE["scripts"].
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
        # if an ichor script, you have to do SCRIPT_NAMES["ichor"]["gaussian"] as
        # SCRIPT_NAMES["ichor"] retruns a ScriptNames type object
        # then the second time this object is indexed with ["gaussian"], it will
        # be an instance of "str", so this if statement will be executed
        if isinstance(script, (str, Path)):
            # append the script name to the path where the scripts are
            # located and modify script name with self.modify
            return self.parent.value / (script + self.modify.value)
        else:
            return script
