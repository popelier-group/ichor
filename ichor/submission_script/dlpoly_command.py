from pathlib import Path
from typing import List

from ichor.common.functools import classproperty
from ichor.logging import logger
from ichor.modules import DlpolyModules, Modules
from ichor.submission_script.command_line import CommandLine


class DlpolyCommand(CommandLine):
    """Class used to construct a Dlpoly job. Jobs are submitted using the `SubmissionScript` class.

    :param dlpoly_directory: Path to where the working directory for dlpoly.
    """

    def __init__(self, dlpoly_directory: Path):
        self.dlpoly_directory = dlpoly_directory

    @property
    def data(self) -> List[str]:
        return [str(self.dlpoly_directory.absolute())]

    @classproperty
    def modules(self) -> Modules:
        """Return a string corresponding to modules that need to be loaded for dlpoly jobs to run on compute nodes."""
        return DlpolyModules

    @classproperty
    def command(self) -> str:
        """Return the command word that is used to run dlpoly. Since it is an executable, it can be ran by calling the path of dlpoly followed by any
        configuration settings."""
        from ichor.globals import GLOBALS

        if not GLOBALS.DLPOLY_LOCATION.is_file():
            logger.warning(
                f"Cannot find DLPOLY location ({GLOBALS.DLPOLY_LOCATION})"
            )
        return str(GLOBALS.DLPOLY_LOCATION.absolute())

    @classproperty
    def ncores(self) -> int:
        """Return the number of cores to be used for ferebus jobs."""

        from ichor.globals import GLOBALS

        return GLOBALS.DLPOLY_NCORES

    def repr(self, variables: List[str]) -> str:
        """Return a string that is used to construct ferebus job files."""
        cmd = f"pushd {variables[0]}\n"
        cmd += f"  {DlpolyCommand.command}\n"
        cmd += "popd\n"
        return cmd
