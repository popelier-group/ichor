import re
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

from ichor import patterns
from ichor.atoms import Atom, Atoms
from ichor.common.functools import buildermethod, classproperty
from ichor.files.file import File, FileContents
from ichor.files.qcp import QuantumChemistryProgramInput


class GaussianJobType(Enum):
    """Enum that give variable names to some of the keywords used in a Gaussian job."""

    Energy = "p"
    Optimisation = "opt"
    Frequency = "freq"

    @classmethod
    def types(cls) -> List[str]:
        return [ty.value for ty in GaussianJobType]


class GJF(QuantumChemistryProgramInput):
    """Wraps around a .gjf file that is used as input to Gaussian."""

    def __init__(self, path: Union[Path, str]):
        QuantumChemistryProgramInput.__init__(self, path)

        self.job_type: Optional[GaussianJobType] = FileContents

        self.charge: Optional[int] = FileContents
        self.multiplicity: Optional[int] = FileContents

        self.startup_options: Optional[List[str]] = FileContents
        self.keywords: Optional[List[str]] = FileContents

    @buildermethod
    def _read_file(self):
        """Parse and red a .gjf file for information we need to submit a Gaussian job."""
        self.atoms = Atoms()
        with open(self.path, "r") as f:
            for line in f:
                # These are Link 0 Commands in Gaussian, eg. %chk
                if line.startswith("%"):
                    if self.startup_options is FileContents:
                        self.startup_options = []
                    self.startup_options += [line.strip().replace("%", "")]
                # This is the following line where key words for Gaussian (level of theory, etc.) are defined
                if line.startswith("#"):
                    line = line.replace("#", "")
                    keywords = line.split()  # split keywords by whitespace
                    for keyword in keywords:
                        if (
                            "/" in keyword
                        ):  # if the user has used something like B3LYP/6-31G Then split them up
                            self.method = keyword.split("/")[0].upper()
                            self.basis_set = keyword.split("/")[1].lower()
                        # if the keyword is in the job enum GaussianJobType: p, opt, freq
                        elif keyword in GaussianJobType.types():
                            for ty in GaussianJobType:
                                if keyword == ty:
                                    # set self.job_type to the enum value corresponding to the keyword
                                    self.job_type = ty
                                    break
                        # if the given Gaussian keyword is not defined in GaussianJobType or is not level of theory/basis set
                        # then add to self.keywords which is None by Default
                        else:
                            if self.keywords is FileContents:
                                self.keywords = []
                            self.keywords += [keyword]
                # find charge and multiplicity which are given on one line in Gaussian .gjf
                if re.match(r"^\s*\d+\s+\d+$", line):
                    self.charge = int(line.split()[0])
                    self.multiplicity = int(line.split()[1])
                # find all the types of atoms as well as their coordinates from .gjf file
                if re.match(patterns.COORDINATE_LINE, line):
                    line_split = line.strip().split()
                    atom_type, x, y, z = (
                        line_split[0],
                        float(line_split[1]),
                        float(line_split[2]),
                        float(line_split[3]),
                    )
                    # add the coordinate line as an Atom instance to self.atoms (which is an Atoms instance)
                    self.atoms.add(Atom(atom_type, x, y, z))

    @classproperty
    def filetype(cls) -> str:
        """Returns the extension of the GJF file."""
        return ".gjf"

    @property
    def title(self) -> str:
        """The name of the system."""
        return self.path.stem

    @property
    def wfn(self):
        """The name of the .wfn file to be returned by Gaussian."""
        return self.path.with_suffix(".wfn")

    @property
    def header_line(self) -> str:
        """Returns a string that is the line in the gjf file that contains all keywords."""
        return f"#{self.job_type.value} {self.method}/{self.basis_set} {' '.join(map(str, self.keywords))}\n"

    def format(self):
        """Format the .gjf file to use Gaussian keywords/variables that are defined in ICHOR GLOBALS."""
        from ichor.globals import GLOBALS

        self.job_type = GaussianJobType.Energy
        self.charge = 0
        self.multiplicity = 1

        self.keywords = []
        required_keywords = ["nosymm", "output=wfn"]
        self.keywords = list(
            set(self.keywords + GLOBALS.KEYWORDS + required_keywords)
        )

        self.method = GLOBALS.METHOD
        self.basis_set = GLOBALS.BASIS_SET

        self.startup_options = [
            f"nproc={GLOBALS.GAUSSIAN_NCORES}",
            f"mem={GLOBALS.GAUSSIAN_MEMORY_LIMIT}",
        ]

    def write(self) -> None:
        """Write the .gjf file to disk. This overwrites .gjf files that currently exist in the path to add any extra options that
        should be given to Gaussian."""
        self.format()
        with open(self.path, "w") as f:
            # TODO: the self.format() results in NoFileFound because of the `class File` implementation. So it has to be inside here.
            for startup_option in self.startup_options:
                f.write(f"%" + startup_option + "\n")
            f.write(f"{self.header_line}\n")
            f.write(f"{self.title}\n\n")
            f.write(f"{self.charge} {self.multiplicity}\n")
            for atom in self.atoms:
                f.write(f"{atom.type} {atom.coordinates_string}\n")
            f.write(f"\n{self.wfn}")
