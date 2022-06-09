from pathlib import Path
from typing import List, Optional

from ichor.core.common.functools import classproperty
from ichor.hpc.modules import Modules, TycheModules
from ichor.hpc.programs import get_tyche_path
from ichor.hpc.submission_script.command_line import CommandLine
from ichor.hpc.submission_script.gaussian_command import GaussianCommand


class TycheCommand(CommandLine):
    """
    todo: write docs
    """

    def __init__(
        self,
        freq_param: Path,
        g09_input: Path,
    ):
        self.freq_param = freq_param
        self.g09_input = g09_input

    @classproperty
    def group(self) -> bool:
        return False

    @property
    def data(self) -> List[str]:
        """Return a list of the absolute paths of the Gaussian input file (.gjf) and the output file (.gau)"""
        return [
            str(self.freq_param.absolute()),
            str(self.g09_input.absolute()),
        ]

    @classproperty
    def modules(self) -> Modules:
        """Returns the modules that need to be loaded in order for Gaussian to work on a specific machine"""
        return TycheModules

    @classproperty
    def command(self) -> str:
        tyche_loc = get_tyche_path()
        return f"{tyche_loc.absolute()}"

    @classproperty
    def ncores(self) -> int:
        """Returns the number of cores that Amber should use for the job."""
        from ichor.hpc import GLOBALS

        return GLOBALS.TYCHE_NCORES

    def repr(self, variables: List[str]) -> str:
        """
        Returns a strings which is then written out to the final submission script file.
        If the outputs of the job need to be checked (by default self.rerun is set to True, so job outputs are checked),
        then the corresponsing strings are appended to the initial commands string.

        The length of `variables` is defined by the length of `self.data`
        """

        freq_param = self.freq_param.absolute()
        g09_input = self.g09_input.absolute()
        gau_output = g09_input.with_suffix(".gau")
        cmd = ""
        cmd += f"pushd {g09_input.parent}\n"
        cmd += f"{GaussianCommand(g09_input).repr([str(g09_input), str(gau_output)])}\n"
        cmd += f"mv fort.* {g09_input.with_suffix('.dev')}"
        cmd += f"cp *.wfn *.dev {freq_param.parent}\n"
        cmd += "popd\n"
        cmd += f"pushd {freq_param.parent}\n"
        cmd += "if [ -f tyche.log ]; then\n"
        cmd += f"  {TycheCommand.command} clean"
        cmd += f"fi\n"
        cmd += f"{TycheCommand.command}\n"
        cmd += "popd\n"

        return cmd
