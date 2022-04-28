import re
from pathlib import Path
from typing import Union

from ichor.atoms import Atom, Atoms
from ichor.common.functools import buildermethod, classproperty
from ichor.common.str import split_by
from ichor_lib.constants import AIMALL_FUNCTIONALS
from ichor.files.file import FileContents
from ichor.files.geometry import GeometryFile, GeometryDataFile
from ichor_lib.units import AtomicDistance
import warnings


class WFN(GeometryFile, GeometryDataFile):
    """Wraps around a .wfn file that is the output of Gaussian. The .wfn file is
    an output file, so it does not have a write method.
    
    :param path: Path object or string to the .wfn file
    :param method: The method (eg. B3LYP) which was used in the Gaussian calculation
        that created the .wfn file. The method is not initially written to the .wfn
        file by Gaussian, but it is necessary to add it to the .wfn file because
        AIMAll does not automatically determine the method itself, so it can lead
        to wrong IQA/multipole moments results. To make sure AIMAll results are correct,
        the method is a required argument.
    :param mol_orbitals: The number of molecular orbitals to be read in from the .wfn file.
    :param primitives: The number of primitives to be read in from the .wfn file.
    :param nuclei: The number of nuclei in the system to be read in from the .wfn file.
    :param energy: The molecular energy read in from the bottom of the .wfn file
    :param virial: The virial read in from the bottom of the .wfn file
    :param atoms: an Atoms instance which is read in from the top of the .wfn file.
        Note that the units of the .wfn file are in Bohr.
    """

    def __init__(self, path: Union[Path, str],
    method: str,
    header: str = FileContents,
    mol_orbitals: int = FileContents,
    primitives: int = FileContents,
    nuclei: int = FileContents,
    energy: float = FileContents,
    virial: float = FileContents,
    atoms: Atoms = FileContents
    ):
        super().__init__(path)

        method = method.upper()
        if method not in AIMALL_FUNCTIONALS:
            warnings.warn("method is not in AIMAll functionals. This will lead to \
                    wrong IQA energies / multipole moments calculated by AIMAll as it \
                    does not determine the method automatically and assumes Hartree-Fock \
                    exchange functional is used..")

        self.header = header
        self.mol_orbitals = mol_orbitals
        self.primitives = primitives
        self.nuclei = nuclei
        self.method = method
        self.energy = energy
        self.virial = virial
        self.atoms = atoms

        # need to call it here, so that it is always modified when a WFN instance is created
        self.modify_header()

    @buildermethod
    def _read_file(self):
        """Parse through a .wfn file to look for the relevant information. This is automatically called if an attribute is being accessed, but the
        FileState of the file is FileState.Unread"""
        self.atoms = Atoms()
        with open(self.path, "r") as f:
            lines = f.readlines()
            lines_iterator = iter(lines)
            next(lines_iterator)
            self.header = next(lines_iterator)
            # modify header line to contain the method used
            self.read_header()
            for line in lines:
                if "CHARGE" in line:
                    try:
                        record = split_by(line, [4, 4, 16, 12, 12, 12])
                        atom_type = record[0]
                        x = float(record[3])
                        y = float(record[4])
                        z = float(record[5])
                    except ValueError:
                        # WFN line using free-formatting
                        record = line.split()
                        atom_type = record[0]
                        x = float(record[4])
                        y = float(record[5])
                        z = float(record[6])

                    self.atoms.add(
                        Atom(atom_type, x, y, z, units=AtomicDistance.Bohr)
                    )
                # this line follows all the coordinates
                # have read all the atom coordinates when we get to it.
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
        """Read in the top of the wavefunction file, currently the data is not used but could be useful.
        .. note::
            The .wfn file written out by Gaussian does not contain the method used (B3LYP, etc.).
            However, this information is needed in AIMAll, otherwise AIMAll cannot determine the
            correct method and will most likely give wrong IQA energies /multipole moments
            because it assumes another method was used to make the .wfn file."""

        data = re.findall(r"\s\d+\s", self.header)

        self.mol_orbitals = int(data[0])
        self.primitives = int(data[1])
        self.nuclei = int(data[2])

    def modify_header(self):
        """ Adds the method (eg. B3LYP) to the header line of the .wfn file to make sure
        that AIMAll uses the correct settings."""

        if self.path.exists():
            with open(self.path, "r") as f:
                lines = f.readlines()
                # if the last word of the header line lines[1] is NUCLEI, then append the method
                if lines[1].split()[-1] == "NUCLEI":
                    lines[1] = lines[1].strip() + "   " + self.method + "\n"
            with open(self.path, "w") as f:
                f.writelines(lines)
        else:
            raise FileNotFoundError(f"WFN file with path {self.path} does not exist.")