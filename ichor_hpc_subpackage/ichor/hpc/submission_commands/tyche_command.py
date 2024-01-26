from pathlib import Path
from typing import List

import ichor.hpc.global_variables

from ichor.core.common.functools import classproperty
from ichor.hpc.global_variables import get_param_from_config
from ichor.hpc.submission_command import SubmissionCommand
from ichor.hpc.submission_commands import GaussianCommand


class TycheCommand(SubmissionCommand):
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
    def modules(self) -> list:
        """Returns the modules that need to be loaded in order for Gaussian to work on a specific machine"""
        return get_param_from_config(
            ichor.hpc.global_variables.ICHOR_CONFIG,
            ichor.hpc.global_variables.MACHINE,
            "software",
            "tyche",
            "modules",
        )

    @classproperty
    def command(self) -> str:
        return get_param_from_config(
            ichor.hpc.global_variables.ICHOR_CONFIG,
            ichor.hpc.global_variables.MACHINE,
            "software",
            "tyche",
            "executable_path",
        )

    @classproperty
    def ncores(self) -> int:
        """Returns the number of cores that Amber should use for the job."""
        pass

    def repr(self, variables: List[str]) -> str:
        """
        Returns a strings which is then written out to the final submission script file.

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
        cmd += "fi\n"
        cmd += f"{TycheCommand.command}\n"
        cmd += "popd\n"

        return cmd
