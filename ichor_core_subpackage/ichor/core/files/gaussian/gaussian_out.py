from pathlib import Path
from typing import Union, List, Dict

from ichor.core.atoms import Atom, Atoms
from ichor.core.common.functools import classproperty
from ichor.core.files.file import FileContents, ReadFile
from ichor.core.files.file_data import HasAtoms, HasProperties
from ichor.core.common.units import AtomicDistance
from collections import namedtuple

AtomForce = namedtuple("AtomForce", "x y z")
MolecularDipole = namedtuple("MolecularDipole", "x y z total")
MolecularQuadrupole = namedtuple("MolecularQuadrupole", "xx yy zz xy xz yz")
TracelessMolecularQuadrupole = namedtuple("TracelessMolecularQuadrupole", "xx yy zz xy xz yz")
MolecularOctapole = namedtuple("MolecularOctapole", "xxx yyy zzz xyy xxy xxz xzz yzz yyz xyz")
MolecularHexadecapole = namedtuple("MolecularHexadecapole", "xxxx yyyy zzzz xxxy xxxz yyyx yyyz zzzx zzzy xxyy xxzz yyzz xxyz yyxz zzxy")

class GaussianOut(HasAtoms, HasProperties, ReadFile):
    """Wraps around a .gau/.log file that is the output of Gaussian. This file contains coordinates (in Angstroms),
    forces, as well as molecular multipole moments.

    :param path: Path object or string to the .gau or .log file that are Gaussian output files
    """

    def __init__(
        self,
        path: Union[Path, str],
    ):
        self.forces = FileContents
        self.charge = FileContents
        self.multiplicity = FileContents
        self.atoms = FileContents
        self.molecular_dipole = FileContents
        self.molecular_quadrupole = FileContents
        self.traceless_molecular_quadrupole = FileContents
        self.molecular_octapole = FileContents
        self.molecular_hexadecapole = FileContents
        super(ReadFile, self).__init__(path)

    def _read_file(self):
        """Parse through a .wfn file to look for the relevant information. This is automatically called if an attribute is being accessed, but the
        FileState of the file is FileState.Unread"""

        atoms = Atoms()                        
        forces = {}

        with open(self.path, "r") as f:
            
            for line in f:
                
                if "Charge =" in line:
                    
                    self.charge, self.multiplicity = int(line.split()[2]), int(line.split()[-1])
                    line = next(f)
                    
                    while line.strip():
                        l = line.split()
                        atom_type = l[0]
                        x = float(l[1])
                        y = float(l[2])
                        z = float(l[3])
                        atoms.add(
                            Atom(
                                atom_type,
                                x,
                                y,
                                z,
                                units=AtomicDistance.Angstroms,
                            )
                        )
                        line = next(f)
                        
                elif "Forces (Hartrees/Bohr)" in line:
                    
                    #  Number     Number              X              Y              Z
                    line = next(f)
                    # -----------------------------------------
                    line = next(f)
                    
                    for atom_name in atoms.names:
                        line = next(f).split()
                        print(line)
                        forces[atom_name] = AtomForce(float(line[2]), float(line[3]), float(line[4]))
                elif "Dipole moment (field-independent basis, Debye)" in line:
                    # dipoles are on one line
                    dipole_line_split = next(f).split()
                    # every 2nd value is a dipole component
                    values = [float(dipole_line_split[i]) for i in range(len(dipole_line_split)) if i%2 != 0]
                    self.molecular_dipole = MolecularDipole(*values)
                elif "Quadrupole moment (field-independent basis, Debye-Ang)" in line:
                    quadrupole_lines_split = (next(f) + next(f)).replace("\n", "   ").split()
                    values = [float(quadrupole_lines_split[i]) for i in range(len(quadrupole_lines_split)) if i%2 != 0]
                    self.molecular_quadrupole = MolecularQuadrupole(*values)
                    
                    # this is the line that says Traceless Quadrupole moment, the problem is that it contains the same text
                    # as the other quadrupole line
                    line = next(f)
                    
                    traceless_quadrupole_lines_split = (next(f) + next(f)).replace("\n", "   ").split()
                    values = [float(traceless_quadrupole_lines_split[i]) for i in range(len(traceless_quadrupole_lines_split)) if i%2 != 0]
                    self.traceless_molecular_quadrupole = TracelessMolecularQuadrupole(*values)
                elif "Octapole moment (field-independent basis, Debye-Ang**2)" in line:
                    octapole_lines_split = (next(f) + next(f) + next(f)).replace("\n", "   ").split()
                    values = [float(octapole_lines_split[i]) for i in range(len(octapole_lines_split)) if i%2 != 0]
                    self.molecular_octapole = MolecularOctapole(*values)
                elif "Hexadecapole moment (field-independent basis, Debye-Ang**3)" in line:
                    hexadecapole_lines_split = (next(f) + next(f) + next(f) + next(f)).replace("\n", "   ").split()
                    values = [float(hexadecapole_lines_split[i]) for i in range(len(hexadecapole_lines_split)) if i%2 != 0]
                    self.molecular_hexadecapole = MolecularHexadecapole(*values)

        self.forces = forces
        self.atoms = atoms

    @classproperty
    def filetype(cls) -> str:
        """Returns the file extension of a WFN file"""
        return ".wfn"

    @classproperty
    def property_names(self) -> List[str]:
        return ["forces"]

    @property
    def properties(self) -> Dict[str, float]:
        return {"forces": self.forces}