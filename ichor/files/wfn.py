import re
from pathlib import Path
from typing import Union

from ichor.atoms import Atom, Atoms
from ichor.common.functools import buildermethod, classproperty
from ichor.common.str import split_by
from ichor.constants import AIMALL_FUNCTIONALS
from ichor.files.file import File, FileContents
from ichor.files.geometry import GeometryDataFile, GeometryFile
from ichor.globals import GLOBALS
from ichor.units import AtomicDistance


class WFN(GeometryFile, GeometryDataFile, File):
    """Wraps around a .wfn file that is the output of Gaussian"""

    def __init__(self, path: Union[Path, str]):
        File.__init__(self, path)
        GeometryFile.__init__(self)
        GeometryDataFile.__init__(self)

        self.header: str = ""

        self.mol_orbitals: int = FileContents
        self.primitives: int = FileContents
        self.nuclei: int = FileContents
        self.method: str = FileContents

        self.energy: float = FileContents
        self.virial: float = FileContents

    @buildermethod
    def _read_file(self, only_header=False):
        """Parse through a .wfn file to look for the relevant information. This is automatically called if an attribute is being accessed, but the
        FileState of the file is FileState.Unread"""
        self.method = GLOBALS.METHOD
        self.atoms = Atoms()
        with open(self.path, "r") as f:
            next(f)
            self.header = next(f)
            self.read_header()
            if only_header:
                return
            for line in f:
                if "CHARGE" in line:
                    record = split_by(line, [4, 4, 16, 12, 12, 12])
                    atom_type = record[0]
                    x = float(record[3])
                    y = float(record[4])
                    z = float(record[5])
                    self.atoms.add(
                        Atom(atom_type, x, y, z, units=AtomicDistance.Bohr)
                    )
                if "CENTRE ASSIGNMENTS" in line:
                    self.atoms.to_angstroms()
                if "TOTAL ENERGY" in line:
                    self.energy = float(line.split()[3])
                    self.virial = float(line.split()[-1])

    @classproperty
    def filetype(cls) -> str:
        """Returns the file extension of a WFN file"""
        return ".wfn"

    def read_header(self):
        """Read in the top of the wavefunction file, currently the data is not used but could be useful
        Following the 'just in case' mentality"""
        from ichor.globals import GLOBALS

        data = re.findall(r"\s\d+\s", self.header)

        self.mol_orbitals = int(data[0])
        self.primitives = int(data[1])
        self.nuclei = int(data[2])

        split_header = self.header.split()
        if split_header[-1] != "NUCLEI":
            self.method = split_header[-1]
        else:
            self.method = GLOBALS.METHOD

    @property
    def title(self):
        """Returns the name of the WFN file (excluding the .wfn extension)"""
        return self.path.stem

    def check_header(self):
        """Checks if the correct Gaussian method (eg. B3LYP) is being used in the Gaussian calculations."""

        if GLOBALS.METHOD in AIMALL_FUNCTIONALS:
            data = []
            with open(self.path, "r") as f:
                for i, line in enumerate(f):
                    if i == 1:
                        if GLOBALS.METHOD.upper() not in line.upper():
                            f.seek(0)
                            data = f.readlines()
                        break

            if data:
                data[1] = data[1].strip() + "   " + str(GLOBALS.METHOD) + "\n"
                with open(self.path, "w") as f:
                    f.writelines(data)
