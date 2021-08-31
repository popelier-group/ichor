import re

from ichor.atoms import Atom, Atoms
from ichor.common.functools import buildermethod, classproperty
from ichor.files.file import File
from ichor.geometry import Geometry, GeometryData
from ichor.units import AtomicDistance


class WFN(Geometry, GeometryData, File):
    """Wraps around a .wfn file that is the output of Gaussian"""
    def __init__(self, path):
        File.__init__(self, path)
        Geometry.__init__(self)
        GeometryData.__init__(self)

        self.header: str = ""

        self.mol_orbitals: int = 0
        self.primitives: int = 0
        self.nuclei: int = 0
        self.method: str = "HF"

    @buildermethod
    def _read_file(self, only_header=False):
        """ Parse through a .wfn file to look for the relevant information. This is automatically called if an attribute is being accessed, but the
        FileState of the file is FileState.Unread"""
        self.atoms = Atoms()
        with open(self.path, "r") as f:
            next(f)
            self.header = next(f)
            self.read_header()
            if only_header:
                return
            for line in f:
                if "CHARGE" in line:
                    line_split = line.split()
                    reline = re.finditer(
                        r"[+-]?\d+\.\d+([[Ee]?[+-]?]\d+)?", line
                    )
                    atom_type, x, y, z = (
                        line_split[0],
                        float(next(reline).group(0)),
                        float(next(reline).group(0)),
                        float(next(reline).group(0)),
                    )
                    self.atoms.add(
                        Atom(atom_type, x, y, z, units=AtomicDistance.Bohr)
                    )
                if "CENTRE ASSIGNMENTS" in line:
                    self.atoms.to_angstroms()
                if "TOTAL ENERGY" in line:
                    self.data.energy = float(line.split()[3])
                    self.data.virial = float(line.split()[-1])

    @classproperty
    def filetype(cls) -> str:
        """ Returns the file extension of a WFN file"""
        return ".wfn"

    def read_header(self):
        """ Read in the top of the wavefunction file, currently the data is not used but could be useful
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
        """ Returns the name of the WFN file (excluding the .wfn extension)"""
        return self.path.stem

    def check_header(self):
        """ Checks if the correct Gaussian method (eg. B3LYP) is being used in the Gaussian calculations."""
        from ichor.globals import GLOBALS

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
