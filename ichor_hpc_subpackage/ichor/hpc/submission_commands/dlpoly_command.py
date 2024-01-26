from pathlib import Path
from typing import List

import ichor.hpc.global_variables

from ichor.core.common.functools import classproperty
from ichor.hpc.global_variables import get_param_from_config
from ichor.hpc.submission_command import SubmissionCommand


class DlpolyCommand(SubmissionCommand):
    """Class used to construct a Dlpoly job. Jobs are submitted using the `SubmissionScript` class.

    :param dlpoly_directory: Path to where the working directory for dlpoly.
    """

    def __init__(self, dlpoly_program_path: Path, dlpoly_directory: Path):

        self.dlpoly_program_path = dlpoly_program_path
        self.dlpoly_directory = dlpoly_directory

    @property
    def data(self) -> List[str]:
        return [str(self.dlpoly_directory.absolute())]

    # TODO: need to load in modules with compiles for dlpoly for submission scripts
    @classproperty
    def modules(self) -> list:
        """No modules need to be loaded for DL POLY. DL POLY needs to be compiled before it can be used with ICHOR."""
        return get_param_from_config(
            ichor.hpc.global_variables.ICHOR_CONFIG,
            ichor.hpc.global_variables.MACHINE,
            "software",
            "dlpoly",
            "modules",
        )

    @property
    def command(self) -> str:
        """Return the command word that is used to run DL POLY. In this case, the path to the DL POLY
        executable is returned."""
        return get_param_from_config(
            ichor.hpc.global_variables.ICHOR_CONFIG,
            ichor.hpc.global_variables.MACHINE,
            "software",
            "dlpoly",
            "executable_path",
        )

    def repr(self, variables: List[str]) -> str:
        """Return a string that is used to construct DL POLY job files."""
        cmd = f"pushd {variables[0]}\n"
        cmd += f"{self.command} &> Energies\n"
        cmd += "popd\n"
        return cmd
