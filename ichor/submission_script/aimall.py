from pathlib import Path
from typing import Tuple
from ichor.modules import AIMAllModules, Modules
from typing import List, Optional

from ichor.common.functools import classproperty
from ichor.globals import GLOBALS
from ichor.globals import Machine
from ichor.submission_script.command_line import CommandLine, SubmissionError


class AIMAllCommand(CommandLine):
    def __init__(self, wfn_file: Path, aimall_output: Optional[Path] = None):
        self.wfn_file = wfn_file
        self.aimall_output = aimall_output or wfn_file.with_suffix(".aim")
        self.atoms = "all"

    @property
    def data(self) -> List[str]:
        return [str(self.wfn_file.absolute()), str(self.aimall_output.absolute())]

    @classproperty
    def modules(self) -> Modules:
        return AIMAllModules

    @classproperty
    def command(self) -> str:
        if GLOBALS.MACHINE is Machine.csf3:
            return "~/AIMAll/aimqb.ish"
        elif GLOBALS.MACHINE is Machine.ffluxlab:
            return "aimall"
        elif GLOBALS.MACHINE is Machine.local:
            return "aimall_test"
        raise SubmissionError(f"Command not defined for '{self.__name__}' on '{GLOBALS.MACHINE.name}'")

    @classproperty
    def options(self) -> List[str]:
        return [
            "-j y",
            "-S /bin/bash"
        ]

    @property
    def arguments(self) -> List[str]:
        return [
            "-nogui",
            "-usetwoe=0",
            f"-atoms={self.atoms}",
            f"-encomp={GLOBALS.ENCOMP}",
            f"-boaq={GLOBALS.BOAQ}",
            f"-iasmesh={GLOBALS.IASMESH}",
            f"-nproc={self.ncores}",
            f"-naat={self.ncores if self.atoms == 'all' else 1}",
        ]


    @classproperty
    def ncores(self) -> int:
        return GLOBALS.AIMALL_CORE_COUNT

    def repr(self, variables: List[str]) -> str:
        return f"{self.command} {' '.join(self.arguments)} {variables[0]} &> {variables[1]}"
