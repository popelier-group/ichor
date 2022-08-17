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
    """Wraps around a .wfn file that is the output of Gaussian. The .wfn file is
    an output file, so it does not have a write method.

    :param path: Path object or string to the .wfn file
    :param atoms: an Atoms instance which is read in from the top of the .wfn file.
        Note that the units of the .wfn file are in Bohr.
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
    .. note::
        Since the wfn file is written out by Gaussian, we do not really have to modify it when writing out except
        we need to add the method used, so that AIMALL can use the correct method. Otherwise AIMALL assumes Hartree-Fock
        was used, which might be wrong.
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
                        print(line)
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
                    line = next(f)
                    
                    for atom_name in atoms.names:
                        line = next(f).split()
                        forces[atom_name] = AtomForce(float(line[3]), float(line[4]), float(line[5]))
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