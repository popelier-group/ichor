from pathlib import Path
from typing import List, Optional, Union

from ichor.common.functools import classproperty
from ichor.common.str import get_digits
from ichor.files import WFN
from ichor.globals import Machine
from ichor.modules import AIMAllModules, Modules
from ichor.submission_script.check_manager import CheckManager
from ichor.submission_script.command_line import CommandLine, SubmissionError


class AIMAllCommand(CommandLine):
    def __init__(
        self,
        wfn_file: Path,
        atoms: Optional[Union[str, List[str]]] = None,
        aimall_output: Optional[Path] = None,
        check: bool = True,
    ):
        self.wfn_file = WFN(wfn_file)
        self.aimall_output = aimall_output or wfn_file.with_suffix(".aim")
        self.atoms = atoms or "all"
        if (
            not isinstance(self.atoms, str)
            and self.wfn_file.exists()
            and len(self.atoms) == len(self.wfn_file.atoms)
        ):
            self.atoms = "all"  # Might as well use atoms=all if all atoms are being calculated
        self.check = check

    @property
    def data(self) -> List[str]:
        return [
            str(self.wfn_file.path.absolute()),
            str(self.aimall_output.absolute()),
        ]

    @classproperty
    def modules(self) -> Modules:
        return AIMAllModules

    @classproperty
    def command(self) -> str:
        from ichor.globals import GLOBALS

        if GLOBALS.MACHINE is Machine.csf3:
            return "~/AIMAll/aimqb.ish"
        elif GLOBALS.MACHINE is Machine.ffluxlab:
            return "aimall"
        elif GLOBALS.MACHINE is Machine.local:
            return "aimall_test"
        raise SubmissionError(
            f"Command not defined for '{self.__name__}' on '{GLOBALS.MACHINE.name}'"
        )

    @classproperty
    def options(self) -> List[str]:
        """ Options taken from GAIA to run AIMAll likely not necessary as we specifiy /bin/bash at the top of the
        submission script

        Note: '-j y' removed from these options from the GAIA version as this outputted both stdout and stderr to
              stdout whereas we want them to be put in the files we specify with the -o and -e flags separately
        """
        return ["-S /bin/bash"]

    @property
    def arguments(self) -> List[str]:
        from ichor.globals import GLOBALS

        atoms = (
            self.atoms
            if isinstance(self.atoms, str)
            else ",".join(map(str, [get_digits(a) for a in self.atoms]))
        )

        return [
            "-nogui",
            "-usetwoe=0",
            f"-atoms={atoms}",
            f"-encomp={GLOBALS.ENCOMP}",
            f"-boaq={GLOBALS.BOAQ}",
            f"-iasmesh={GLOBALS.IASMESH}",
            f"-nproc={self.ncores}",
            f"-naat={self.ncores if self.atoms == 'all' else min(len(self.atoms), self.ncores)}",
        ]

    @classproperty
    def ncores(self) -> int:
        from ichor.globals import GLOBALS

        return GLOBALS.AIMALL_CORE_COUNT

    def repr(self, variables: List[str]) -> str:
        cmd = f"{AIMAllCommand.command} {' '.join(self.arguments)} {variables[0]} &> {variables[1]}"

        if self.check:
            from ichor.globals import GLOBALS

            cm = CheckManager(
                check_function="check_aimall_output",
                args_for_check_function=[variables[0]],
                ntimes=GLOBALS.AIMALL_N_TRIES,
            )
            return cm.check(cmd)
        else:
            return cmd
