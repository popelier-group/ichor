from pathlib import Path
from typing import List, Optional

from ichor.common.functools import classproperty
from ichor.globals import Machine
from ichor.modules import GaussianModules, Modules
from ichor.submission_script.check_manager import CheckManager
from ichor.submission_script.command_line import CommandLine, SubmissionError


class GaussianCommand(CommandLine):
    def __init__(
        self,
        gjf_file: Path,
        gjf_output: Optional[Path] = None,
        check: bool = True,
    ):
        self.gjf_file = gjf_file
        self.gjf_output = gjf_output or gjf_file.with_suffix(".gau")
        self.check = check

    @property
    def data(self) -> List[str]:
        return [str(self.gjf_file.absolute()), str(self.gjf_output.absolute())]

    @classproperty
    def modules(self) -> Modules:
        return GaussianModules

    @classproperty
    def command(self) -> str:
        from ichor.globals import GLOBALS

        if GLOBALS.MACHINE is Machine.csf3:
            return "$g09root/g09/g09"
        elif GLOBALS.MACHINE is Machine.ffluxlab:
            return "g09"
        elif GLOBALS.MACHINE is Machine.local:
            return "g09_test"
        raise SubmissionError(
            f"Command not defined for '{self.__name__}' on '{GLOBALS.MACHINE.name}'"
        )

    @classproperty
    def ncores(self) -> int:
        from ichor.globals import GLOBALS

        return GLOBALS.GAUSSIAN_CORE_COUNT

    def repr(self, variables: List[str]) -> str:
        cmd = f"{self.command} {variables[0]} {variables[1]}"

        if self.check:
            from ichor.globals import GLOBALS

            cm = CheckManager(
                check_function="check_gaussian_output",
                check_args=[variables[0]],
                ntimes=GLOBALS.GAUSSIAN_N_TRIES,
            )
            return cm.check(cmd)
        else:
            return cmd
