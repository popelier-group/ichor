from pathlib import Path
from typing import List

from ichor.core.common.functools import classproperty
from ichor.hpc.log import logger
from ichor.hpc.modules import DlpolyModules, Modules
from ichor.hpc.programs import get_dlpoly_path
from ichor.hpc.submission_script.command_line import CommandLine


class DlpolyCommand(CommandLine):
    """Class used to construct a Dlpoly job. Jobs are submitted using the `SubmissionScript` class.

    :param dlpoly_directory: Path to where the working directory for dlpoly.
    """

    def __init__(self, dlpoly_program_path: Path, dlpoly_directory: Path , ncores: int = 1):
        
        self.dlpoly_program_path = dlpoly_program_path
        self.dlpoly_directory = dlpoly_directory
        self.ncores = ncores

    @property
    def data(self) -> List[str]:
        return [str(self.dlpoly_directory.absolute())]

    @classproperty
    def modules(self) -> Modules:
        """Return a string corresponding to modules that need to be loaded for dlpoly jobs to run on compute nodes."""
        return DlpolyModules

    @property
    def command(self) -> str:
        """Return the command word that is used to run dlpoly. Since it is an executable, it can be ran by calling the path of dlpoly followed by any
        configuration settings."""
        return str(self.dlpoly_program_path.absolute())

    def repr(self, variables: List[str]) -> str:
        """Return a string that is used to construct ferebus job files."""
        cmd = f"pushd {variables[0]}\n"
        cmd += f"  {self.command}\n"
        cmd += "popd\n"
        return cmd
