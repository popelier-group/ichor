from pathlib import Path
from typing import Union, List, Dict

from ichor.core.atoms import Atom, Atoms
from ichor.core.common.functools import classproperty
from ichor.core.files.file import FileContents, ReadFile
from ichor.core.files.file_data import HasAtoms, HasProperties
from ichor.core.common.units import AtomicDistance
from ichor.core.common.types.forces import AtomForce, MolecularDipole, MolecularHexadecapole, MolecularOctapole, MolecularQuadrupole, TracelessMolecularQuadrupole
import numpy as np

class GaussianOut(HasAtoms, HasProperties, ReadFile):
    """Wraps around a .gau/.log file that is the output of Gaussian. This file contains coordinates (in Angstroms),
    forces, as well as molecular multipole moments.

    :param path: Path object or string to the .gau or .log file that are Gaussian output files
    """

    def __init__(
        self,
        path: Union[Path, str],
    ):
        self.global_forces = FileContents
        self.charge = FileContents
        self.multiplicity = FileContents
        self.atoms = FileContents
        self.molecular_dipole = FileContents
        self.molecular_quadrupole = FileContents
        self.traceless_molecular_quadrupole = FileContents
        self.molecular_octapole = FileContents
        self.molecular_hexadecapole = FileContents
        super(ReadFile, self).__init__(path)

    @classproperty
    def filetype(self) -> str:
        return ".gau"

    @classproperty
    def property_names(self) -> List[str]:
        return ["forces"]

    # TODO: rotation of Gaussian forces not needed in FFLUX, can directly learn Gaussian forces
    # TODO: FFLUX predicts directly in the global frame so IQA forces should be the same as Gaussian forces
    def properties(self, C_matrix_dict: Dict[str, np.ndarray]) -> Dict[str, Dict[str, AtomForce]]:
        """Returns the machine learning labels which are in this file. The atomic forces need to be rotated by a C matrix
        (each atom has its own C matrix) prior to machine learning. This method is primarily here to be used by
        `PointDirectory`/`PointsDirectory` classes.

        :param C_matrix_dict: A dictionary of C matrices for each atom in the system.
        :type C_matrix_dict: Dict[str, np.ndarray]
        :return: A dictionary of dictionaries. The inner dictionary
            has key: atom_name and value: AtomForce (a namedtuple with rotated forces for that atom).
        :rtype: Dict[str, Dict[str, `AtomForce`]]
        """
        
        return {"forces": self.local_forces(C_matrix_dict)}
    
    def local_forces(self, C_matrix_dict: Dict[str, np.ndarray]) -> Dict[str, AtomForce]:
        """ Rotates the force vector by the C matrix (which defines a new coordinate frame). The C matrix is dependent on
        the atomic local frame calculated for each atom. Each atom has its own C rotation matrix, so each atomic force is
        rotated by the atom's specific C matrix.
        
        :param C_matrix_dict: A dictionary of C matrices for each atom in the system.
        :type C_matrix_dict: Dict[str, np.ndarray]
        :return: A dictionary of dictionaries. The inner dictionary
            has key: atom_name and value: AtomForce (a namedtuple with rotated forces for that atom).
        :rtype: Dict[str, float]
        """

        local_forces = {}

        for atom_name, global_force in self.global_forces.items():
            
            # multiply the force by C matrix for that specific atom, giving local forces
            tmp = np.matmul(C_matrix_dict[atom_name], np.array(global_force))
            # convert to AtomForce type and save to dict
            local_forces[atom_name] = AtomForce(*tmp)
        
        return local_forces

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

        self.global_forces = forces
        self.atoms = atoms