import re
from enum import Enum
from typing import List

from ichor import patterns
from ichor.common.functools import buildermethod, classproperty
from ichor.files.file import File
from ichor.geometry import Geometry
from ichor.atoms import Atom


class GaussianJobType(Enum):
    Energy = "p"
    Optimisation = "opt"
    Frequency = "freq"


class GJF(Geometry, File):
    def __init__(self, path):
        File.__init__(self, path)
        Geometry.__init__(self)

        self.job_type: GaussianJobType = GaussianJobType.Energy
        self.method: str = "b3lyp"
        self.basis_set: str = "6-31+g(d,p)"

        self.charge: int = 0
        self.multiplicity: int = 1

        self.header_line: str = ""

        # self.wfn = WFN(self.path.replace(".gjf", ".wfn"))

        self.startup_options: List[str] = []
        self.keywords: List[str] = []

    @classproperty
    def filetype(cls) -> str:
        return ".gjf"

    @buildermethod
    def _read_file(self):
        with open(self.path, "r") as f:
            for line in f:
                if line.startswith("%"):
                    self.startup_options += [line.strip().replace("%", "")]
                if line.startswith("#"):
                    keywords = line.split()
                    for keyword in keywords:
                        if "/" in keyword:
                            self.method = keyword.split("/")[0].upper()
                            self.basis_set = keyword.split("/")[1].lower()
                if re.match(r"^\s*\d+\s+\d+$", line):
                    self.charge = int(line.split()[0])
                    self.multiplicity = int(line.split()[1])
                if re.match(patterns.COORDINATE_LINE, line):
                    line_split = line.strip().split()
                    atom_type, x, y, z = line_split[0], float(line_split[1]), float(line_split[2]), float(line_split[3])
                    self.atoms.add(Atom(atom_type, x, y, z))

    @property
    def title(self):
        return self.path.stem

    @property
    def wfn(self):
        return self.path.with_suffix(".wfn")

    def format(self):
        from ichor.globals import GLOBALS

        if not self.atoms:
            self.read()

        self.method = GLOBALS.METHOD
        self.basis_set = GLOBALS.BASIS_SET

        required_keywords = ["nosymm", "output=wfn"]
        self.keywords = list(
            set(self.keywords + GLOBALS.KEYWORDS + required_keywords)
        )

        self.startup_options = [
            f"nproc={GLOBALS.GAUSSIAN_CORE_COUNT}",
            f"mem=1GB",  # TODO: Convert this to global variable
        ]

        self.header_line = f"#{self.job_type.value} {self.method}/{self.basis_set} {' '.join(map(str, self.keywords))}\n"

    def write(self):
        self.format()
        with open(self.path, "w") as f:
            for startup_option in self.startup_options:
                f.write(f"%" + startup_option + "\n")
            f.write(f"{self.header_line}\n")
            f.write(f"{self.title}\n\n")
            f.write(f"{self.charge} {self.multiplicity}\n")
            for atom in self.atoms:
                f.write(f"{str(atom)}\n")
            f.write(f"\n{self.wfn}")
