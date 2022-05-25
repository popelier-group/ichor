from pathlib import Path
from typing import List

from ichor.ichor_lib.common.functools import classproperty
from ichor.log import logger
from ichor.modules import FerebusModules, Modules
from ichor.programs import get_ferebus_path
from ichor.submission_script.command_line import CommandLine
from ichor.submission_script.ichor_command import ICHORCommand


class FerebusCommand(CommandLine):
    """Class used to construct a FEREBUS job. Jobs are submitted using the `SubmissionScript` class.

    :param ferebus_directory: Path to where the FEREBUS program is located.
    :param mode_models: Whether or not to move the GP models made by FEREBUS to the MODEL directory.
    """

    def __init__(self, ferebus_directory: Path, move_models: bool = True):
        self.ferebus_directory = ferebus_directory
        self.move_models = move_models

    @property
    def data(self) -> List[str]:
        return [str(self.ferebus_directory.absolute())]

    @classproperty
    def modules(self) -> Modules:
        """Return a string corresponding to modules that need to be loaded for FEREBUS jobs to run on compute nodes."""
        return FerebusModules

    @classproperty
    def command(self) -> str:
        """Return the command word that is used to run FEREBUS. Since it is an executable, it can be ran by calling the path of FEREBUS followed by any
        configuration settings."""
        ferebus_path = get_ferebus_path()
        return str(ferebus_path.absolute())

    @classproperty
    def ncores(self) -> int:
        """Return the number of cores to be used for ferebus jobs."""

        from ichor.ichor_hpc import GLOBALS

        return GLOBALS.FEREBUS_NCORES

    def repr(self, variables: List[str]) -> str:
        """Return a string that is used to construct ferebus job files."""
        cmd = f"pushd {variables[0]}\n"
        cmd += f"  {FerebusCommand.command}\n"
        cmd += "popd\n"
        if self.move_models:
            move_models = ICHORCommand()
            move_models.add_function_to_job("move_models", variables[0])
            cmd += f"{move_models.repr()}\n"
        return cmd
