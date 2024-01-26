from pathlib import Path
from typing import List

import ichor.hpc.global_variables

from ichor.core.common.functools import classproperty
from ichor.hpc.global_variables import get_param_from_config
from ichor.hpc.submission_command import SubmissionCommand


class CP2KCommand(SubmissionCommand):
    """
    todo: write docs
    """

    def __init__(
        self,
        cp2k_input: Path,
        temperature: float,
        ncores: int,
        system_name: str,
    ):
        self.input = cp2k_input
        self.temperature = temperature
        self.ncores = ncores
        self.system_name = system_name

    @classproperty
    def group(self) -> bool:
        return False

    @classproperty
    def modules(self) -> list:
        """Returns the modules that need to be loaded in order for Gaussian to work on a specific machine"""
        return ichor.hpc.global_variables.ICHOR_CONFIG[
            ichor.hpc.global_variables.MACHINE
        ]["software"]["cp2k"]["modules"]

    @property
    def data(self) -> List[str]:
        """Return a list of the absolute paths of the Gaussian input file (.gjf) and the output file (.gau)"""
        return [str(self.input.absolute())]

    @property
    def command(self) -> str:
        """Returns the command to be used to run CP2K. The command depends on the
        number of cores."""
        return get_param_from_config(
            ichor.hpc.global_variables.ICHOR_CONFIG,
            ichor.hpc.global_variables.MACHINE,
            "software",
            "cp2k",
            "executable_path",
        )

    def repr(self, variables: List[str]) -> str:
        """
        Returns a strings which is then written out to the final submission script file.

        The length of `variables` is defined by the length of `self.data`
        """
        input = self.input.absolute()
        cmd = ""
        cmd += f'cp2kdir=$(dirname "{input}")\n'
        cmd += "pushd $cp2kdir\n"
        cmd += f"{self.command} -i {input} -o {input.with_suffix('.out')}\n"
        cmd += "popd\n"

        return cmd
