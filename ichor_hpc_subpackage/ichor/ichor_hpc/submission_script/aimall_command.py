from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

from ichor.ichor_lib.common.functools import classproperty
from ichor.ichor_lib.common.str import get_digits
from ichor.ichor_lib.files import WFN
from ichor.modules import AIMAllModules, Modules
from ichor.submission_script.check_manager import CheckManager
from ichor.submission_script.command_line import CommandLine, SubmissionError


class BasinIntegrationMethod(Enum):
    Auto = "auto"
    ProAIM = "proaim"
    ProMega = "promega"
    ProMega1 = "promega1"
    ProMega5 = "promega5"


class IASMesh(Enum):
    Sparse = "fine"
    Medium = "medium"
    Fine = "fine"
    VeryFine = "veryfine"
    SuperFine = "superfine"


class Capture(Enum):
    Auto = "auto"
    Basic = "basic"
    Extended = "extended"


class Boaq(Enum):
    Auto = "auto"
    AutoGS2 = "auto_gs2"
    AutoGS4 = "auto_gs4"
    GS1 = "gs1"
    GS2 = "gs2"
    GS3 = "gs3"
    GS4 = "gs4"
    GS5 = "gs5"
    GS6 = "gs6"
    GS7 = "gs7"
    GS8 = "gs8"
    GS9 = "gs9"
    GS10 = "gs10"
    GS15 = "gs15"
    GS20 = "gs20"
    GS25 = "gs25"
    GS30 = "gs30"
    GS35 = "gs35"
    GS40 = "gs40"
    GS45 = "gs45"
    GS50 = "gs50"
    GS55 = "gs55"
    GS60 = "gs60"
    Leb23 = "leb23"
    Leb25 = "leb25"
    Leb27 = "leb27"
    Leb29 = "leb29"
    Leb31 = "leb31"
    Leb32 = "leb32"


class Ehren(Enum):
    No = 0
    StressDivergence = 1
    OneElectronGradient = 2


class MagProps(Enum):
    NONE = "none"
    IGAIM = "gaim"
    CSGTB = "csgtb"
    GIAO = "giao"


class ATIDSProps(Enum):
    No = "no"
    Some = "0.001"
    All = "all"


class Encomp(Enum):
    Zero = 0
    One = 1
    Two = 2
    Three = 3
    Four = 4


class SCP(Enum):
    No = "false"
    Some = "some"
    Yes = "true"


class F2W(Enum):
    WFX = "wfx"
    WFN = "wfn"


class MIR(Enum):
    Auto = "auto"
    Custom = "custom"


class CPConn(Enum):
    Moderate = "moderate"
    Complex = "complex"
    Simple = "simple"
    Basic = "basic"


class IntVeeAA(Enum):
    Old = "old"
    New = "new"


class SHMMax(Enum):
    NONE = -1
    Charge = 0
    Dipole = 1
    Quadrupole = 2
    Octupole = 3
    Hexadecapole = 4
    All = 5


class VerifyW(Enum):
    No = "no"
    Yes = "yes"
    Only = "only"


class AIMAllCommand(CommandLine):

    """
    A class which is used to add AIMALL-related commands to a submission script. It is used to write the submission script line where
    AIMALL modules are loaded. It is also used to write out the submission script line where AIMALL is ran on a specified array of files (usually
    AIMALL is ran as an array job because we want to run hundreds of AIMALL tasks in parallel). Finally, depending on the `check` and `scrub` arguments,
    additional lines are written to the submission script file which rerun failed tasks as well as remove any points that did not terminate normally (even
    after being reran).

    :param wfn_file: Path to a .wfn file. This is not needed when running auto-run for a whole directory.
    :param aimall_output: Optional path to the AIMALL job output. Default is None as it is set to the `gjf_file_name`.aim if not specified.
    """

    def __init__(
        self,
        wfn_file: Path,
        atoms: Optional[Union[str, List[str]]] = None,
        aimall_output: Optional[Path] = None,
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
        from ichor.machine.machine import MACHINE, Machine

        if MACHINE is Machine.csf3:
            return "~/AIMAll/aimqb.ish"
        elif MACHINE is Machine.ffluxlab:
            return "aimall"
        elif MACHINE is Machine.local:
            return "aimall_test"
        raise SubmissionError(
            f"Command not defined for '{self.__name__}' on '{MACHINE.name}'"
        )

    @classproperty
    def options(self) -> List[str]:
        """Options taken from GAIA to run AIMAll likely not necessary as we specifiy /bin/bash at the top of the
        submission script

        Note: '-j y' removed from these options from the GAIA version as this outputted both stdout and stderr to
              stdout whereas we want them to be put in the files we specify with the -o and -e flags separately
        """
        return ["-S /bin/bash"]

    @property
    def arguments(self) -> List[str]:
        from ichor.ichor_hpc.globals import GLOBALS

        atoms = (
            self.atoms
            if isinstance(self.atoms, str)
            else "all_"
            + ",".join(map(str, [get_digits(a) for a in self.atoms]))
        )

        return [
            "-nogui",
            "-usetwoe=0",
            f"-atoms={atoms}",
            f"-encomp={Encomp(GLOBALS.AIMALL_ENCOMP).value}",
            f"-boaq={Boaq(GLOBALS.AIMALL_BOAQ).value}",
            f"-iasmesh={IASMesh(GLOBALS.AIMALL_IASMESH).value}",
            f"-nproc={self.ncores}",
            f"-naat={self.ncores if self.atoms == 'all' else min(len(self.atoms), self.ncores)}",
            f"-bim={BasinIntegrationMethod(GLOBALS.AIMALL_BIM).value}",
            f"-capture={Capture(GLOBALS.AIMALL_CAPTURE).value}",
            f"-ehren={Ehren(GLOBALS.AIMALL_EHREN).value}",
            f"-feynman={str(GLOBALS.AIMALL_FEYNMAN).lower()}",
            f"-iasprops={str(GLOBALS.AIMALL_IASPROPS).lower()}",
            f"-magprops={MagProps(GLOBALS.AIMALL_MAGPROPS).value}",
            f"-source={str(GLOBALS.AIMALL_SOURCE).lower()}",
            f"-iaswrite={str(GLOBALS.AIMALL_IASWRITE).lower()}",
            f"-atidsprops={ATIDSProps(GLOBALS.AIMALL_ATIDSPROPS).value}",
            f"-warn={str(GLOBALS.AIMALL_WARN).lower()}",
            f"-scp={SCP(GLOBALS.AIMALL_SCP.lower()).value}",
            f"-delmog={str(GLOBALS.AIMALL_DELMOG).lower()}",
            f"-skipint={str(GLOBALS.AIMALL_SKIPINT).lower()}",
            f"-f2w={F2W(GLOBALS.AIMALL_F2W).value}",
            f"-f2wonly={str(GLOBALS.AIMALL_F2WONLY).lower()}",
            f"-mir={MIR.Auto.value if GLOBALS.AIMALL_MIR < 0 else GLOBALS.AIMALL_MIR}",
            f"-cpconn={CPConn(GLOBALS.AIMALL_CPCONN).value}",
            f"-intveeaa={IntVeeAA(GLOBALS.AIMALL_INTVEEAA).value}",
            f"-atlaprhocps={str(GLOBALS.AIMALL_ATLAPRHOCPS).lower()}",
            f"-wsp={str(GLOBALS.AIMALL_WSP).lower()}",
            f"-shm_lmax={SHMMax(GLOBALS.AIMALL_SHM).value}",
            f"-maxmem={GLOBALS.AIMALL_MAXMEM}",
            f"-verifyw={VerifyW(GLOBALS.AIMALL_VERIFYW).value}",
            f"-saw={str(GLOBALS.AIMALL_SAW).lower()}",
            f"-autonnacps={str(GLOBALS.AIMALL_AUTONNACPS).lower()}",
        ]

    @classproperty
    def ncores(self) -> int:
        from ichor.ichor_hpc.globals import GLOBALS

        return GLOBALS.AIMALL_NCORES

    def repr(self, variables: List[str]) -> str:
        """Returns a string which is written out to the submission script file in order to run AIMALL correctly (with the appropriate settings)."""

        cmd = f"{AIMAllCommand.command} {' '.join(self.arguments)} {variables[0]} &> {variables[1]}"

        from ichor.ichor_hpc.globals import GLOBALS

        if GLOBALS.RERUN_POINTS:

            cm = CheckManager(
                check_function="rerun_aimall",
                args_for_check_function=[variables[0]],
                ntimes=GLOBALS.GAUSSIAN_N_TRIES,
            )
            cmd = cm.rerun_if_job_failed(cmd)

        if GLOBALS.SCRUB_POINTS:
            cm = CheckManager(
                check_function="scrub_aimall",
                args_for_check_function=[variables[0]],
            )
            cmd = cm.scrub_point_directory(cmd)

        return cmd
