from pathlib import Path
from typing import List, Optional

from ichor.core.common.functools import classproperty
from ichor.hpc import GLOBALS
from ichor.hpc.modules import CP2KModules, Modules
from ichor.hpc.submission_script.command_line import CommandLine
from ichor.hpc.submission_script.ichor_command import ICHORCommand


class CP2KCommand(CommandLine):
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
    def modules(self) -> Modules:
        """Returns the modules that need to be loaded in order for Gaussian to work on a specific machine"""
        return CP2KModules

    @property
    def data(self) -> List[str]:
        """Return a list of the absolute paths of the Gaussian input file (.gjf) and the output file (.gau)"""
        return [str(self.input.absolute())]

    @property
    def command(self) -> str:
        """Returns the command to be used to run CP2K. The command depends on the 
        number of cores."""

        if self.ncores == 1:
            return "cp2k.sopt"
        else:
            return f"cp2k.ssmp"

    def repr(self, variables: List[str]) -> str:
        """
        Returns a strings which is then written out to the final submission script file.
        If the outputs of the job need to be checked (by default self.rerun is set to True, so job outputs are checked),
        then the corresponsing strings are appended to the initial commands string.

        The length of `variables` is defined by the length of `self.data`
        """
        input = self.input.absolute()
        cmd = ""
        cmd += f'cp2kdir=$(dirname "{input}")\n'
        cmd += f"pushd $cp2kdir\n"
        cmd += f"{self.command} -i {input} -o {input.with_suffix('.out')}\n"
        cmd += "popd\n"

        return cmd
