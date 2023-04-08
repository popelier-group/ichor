from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

import ichor.hpc.global_variables

from ichor.core.atoms import Atoms
from ichor.core.common.functools import classproperty
from ichor.core.common.str import get_digits
from ichor.core.files import WFN
from ichor.hpc.machine import Machine
from ichor.hpc.modules import AIMAllModules, Modules
from ichor.hpc.submission_command import SubmissionCommand, SubmissionError


class UseTwoe(Enum):

    No = 0
    Vee_aa = 1
    Always = 2


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
    Some = 0.001
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


AIMAll_COMMANDS = {
    Machine.csf3: "~/AIMAll/aimqb.ish",
    Machine.csf4: "~/AIMAll/aimqb.ish",
    Machine.ffluxlab: "aimall",
    Machine.local: "aimall",
}


class AIMAllCommand(SubmissionCommand):
    """
    A class which is used to add AIMALL-related commands to a submission script.
    It is used to write the submission script line where
    AIMALL modules are loaded. It is also used to write out the submission script line where
    AIMALL is ran on a specified array of files (usually
    AIMALL is ran as an array job because we want to run hundreds of AIMALL tasks in parallel).

    :param wfn_file: Path to a .wfn file. This is not needed when running auto-run for a whole directory.
    :param atoms: A list of strings of atom names (e.g. C1)
        which aimall to integrate or an Atoms instance (from which the names will be obtained)
    """

    def __init__(
        self,
        wfn_file_path: Path,
        ncores: int,
        naat: int,
        atoms: Optional[Union[List[str], Atoms]] = "all",
        usetwoe: int = 0,
        encomp: int = 3,
        boaq: str = "auto",
        iasmesh: str = "fine",
        bim: str = "auto",
        capture: str = "auto",
        ehren: int = 0,
        feynman: bool = False,
        iasprops: bool = True,
        magprops: str = "none",
        source: bool = False,
        iaswrite: bool = False,
        atidsprops: float = 0.001,
        warn: bool = True,
        scp: str = "some",
        delmog: bool = True,
        skipint: bool = False,
        f2w: str = "wfx",
        f2wonly: bool = False,
        mir: str = "auto",
        cpconn: str = "moderate",
        intveeaa: str = "new",
        atlaprhocps: bool = False,
        wsp: bool = True,
        shm_lmax: int = 5,
        maxmem: int = 2400,
        verifyw: str = "yes",
        saw: bool = False,
        autonnacps: bool = True,
    ):

        self.wfn_file = WFN(wfn_file_path)

        self.usetwoe = UseTwoe(usetwoe)

        self.atoms = atoms or "all"
        if isinstance(atoms, Atoms):
            self.atoms = list(self.atoms.names)

        self.ncores = ncores
        self.naat = naat
        self.aimall_output = wfn_file_path.with_suffix(".aim")
        self.encomp = Encomp(encomp)
        self.boaq = Boaq(boaq)
        self.iasmesh = IASMesh(iasmesh)
        self.bim = BasinIntegrationMethod(bim)
        self.capture = Capture(capture)
        self.ehren = Ehren(ehren)
        self.feynman = feynman
        self.iasprops = iasprops
        self.magprops = MagProps(magprops)
        self.source = source
        self.iaswrite = iaswrite
        self.atidsprops = ATIDSProps(atidsprops)
        self.warn = warn
        self.scp = SCP(scp)
        self.delmog = delmog
        self.skipint = skipint
        self.f2w = F2W(f2w)
        self.f2wonly = f2wonly
        self.mir = MIR(mir)
        self.cpconn = CPConn(cpconn)
        self.intveeaa = IntVeeAA(intveeaa)
        self.atlaprhocps = atlaprhocps
        self.wsp = wsp
        self.shm_lmax = SHMMax(shm_lmax)
        self.maxmem = maxmem
        self.verifyw = VerifyW(verifyw)
        self.saw = saw
        self.autonnacps = autonnacps

    @property
    def data(self) -> List[str]:
        """Returns the data needed for the AIMAll job to run successfully"""
        return [str(self.wfn_file.path.absolute()), str(self.aimall_output.absolute())]

    @classproperty
    def modules(self) -> Modules:
        """Returns a list of modules to be loaded for AIMAll.
        Note that only ffluxlab has AIMAll as a module.
        For other machines, the AIMAll folder (containing scripts/executables)
        needs to be found in the home directory."""
        return AIMAllModules

    @classproperty
    def command(self) -> str:
        """Returns the command which runs aimall on the current machine.
        Note that only ffluxlab has AIMAll as a module.
        For other machines, the AIMAll folder (containing scripts/executables)
        needs to be found in the home directory."""

        if ichor.hpc.global_variables.MACHINE not in AIMAll_COMMANDS.keys():
            raise SubmissionError(
                f"Command not defined for '{self.__name__}' on '{ichor.hpc.global_variables.MACHINE.name}'"
            )

        return AIMAll_COMMANDS[ichor.hpc.global_variables.MACHINE]

    @property
    def arguments(self) -> List[str]:

        # if all, then no need to change anything
        # if a list of atom names is given, then need to make in format which AIMAll reads

        # -atoms=all_... (e.g., -atoms=all_1,3,6) will calculate a full molecular graph
        # but will only calculate atomic properties of the listed atoms.

        # Specifying -atoms=... (e.g., -atoms=1,3,6)
        # (recommended for specifying problem atoms with large integration error following an all atom run)
        # will only determine the critical point connectivity and atomic properties of the listed atoms,
        # i.e., the full molecular graph will not be (re)calculated.
        atoms = (
            self.atoms
            if self.atoms == "all"
            else "all_" + ", ".join(map(str, [get_digits(a) for a in self.atoms]))
        )

        return [
            "-nogui",
            f"-usetwoe={self.usetwoe.value}",
            f"-nproc={self.ncores}",
            f"-naat={self.naat}",
            f"-atoms={atoms}",
            f"-encomp={self.encomp.value}",
            f"-boaq={self.boaq.value}",
            f"-iasmesh={self.iasmesh.value}",
            f"-bim={self.bim.value}",
            f"-capture={self.capture.value}",
            f"-ehren={self.ehren.value}",
            f"-feynman={str(self.feynman).lower()}",
            f"-iasprops={str(self.iasprops).lower()}",
            f"-magprops={self.magprops.value}",
            f"-source={str(self.source).lower()}",
            f"-iaswrite={str(self.iaswrite).lower()}",
            f"-atidsprops={self.atidsprops.value}",
            f"-warn={str(self.warn).lower()}",
            f"-scp={self.scp.value}",
            f"-delmog={str(self.delmog).lower()}",
            f"-skipint={str(self.skipint).lower()}",
            f"-f2w={self.f2w.value}",
            f"-f2wonly={str(self.f2wonly).lower()}",
            f"-mir={self.mir.value}",
            f"-cpconn={self.cpconn.value}",
            f"-intveeaa={self.intveeaa.value}",
            f"-atlaprhocps={str(self.atlaprhocps).lower()}",
            f"-wsp={str(self.wsp).lower()}",
            f"-shm_lmax={self.shm_lmax.value}",
            f"-maxmem={self.maxmem}",
            f"-verifyw={self.verifyw.value}",
            f"-saw={str(self.saw).lower()}",
            f"-autonnacps={str(self.autonnacps).lower()}",
            f"-iaswrite={str(self.iaswrite)}",
        ]

    def repr(self, variables: List[str]) -> str:
        """Returns a string which is written out to the submission script file in
        order to run AIMALL correctly (with the appropriate settings)."""

        cmd = f"{AIMAllCommand.command} {' '.join(self.arguments)} {variables[0]} &> {variables[1]}"

        return cmd
