from pathlib import Path
from typing import Union

import numpy as np

from ichor.core.atoms import Atom, Atoms
from ichor.core.common.types.multipole_moments import (
    MolecularDipole,
    MolecularHexadecapole,
    MolecularOctapole,
    MolecularQuadrupole,
    TracelessMolecularQuadrupole,
)

from ichor.core.common.units import AtomicDistance
from ichor.core.files.file import FileContents, ReadFile
from ichor.core.files.file_data import HasAtoms, HasData


class GaussianOutput(ReadFile, HasAtoms, HasData):
    """Wraps around a .gaussianoutput file that is the output of Gaussian.
    This file contains coordinates (in Angstroms),
    forces, as well as molecular multipole moments.

    :param path: Path object or string to the .gaussianoutput file that are Gaussian output files
    """

    _filetype = [".gaussianoutput", ".gau"]

    def __init__(
        self,
        path: Union[Path, str],
    ):

        # TODO: potentially implement global_forces as np.array instead of dict
        self.global_forces: dict = FileContents
        self.charge: int = FileContents
        self.multiplicity: int = FileContents
        self.atoms: Atoms = FileContents
        self.molecular_dipole: MolecularDipole = FileContents
        self.molecular_quadrupole: MolecularDipole = FileContents
        self.traceless_molecular_quadrupole: TracelessMolecularQuadrupole = FileContents
        self.molecular_octapole: MolecularOctapole = FileContents
        self.molecular_hexadecapole: MolecularHexadecapole = FileContents
        super(ReadFile, self).__init__(path)

    @property
    def raw_data(self) -> dict:
        return {
            "global_forces": self.global_forces,
            "charge": self.charge,
            "multiplicity": self.multiplicity,
            "molecular_dipole": self.molecular_dipole,
            "molecular_quadrupole": self.molecular_quadrupole,
            "traceless_molecular_quadrupole": self.traceless_molecular_quadrupole,
            "molecular_octapole": self.molecular_octapole,
            "molecular_hexadecapole": self.molecular_hexadecapole,
        }

    def rotated_forces(self, rotation_matrix: np.ndarray) -> dict:
        """Rotates forces gives a rotation_matrix, which could be the C matrix
        to rotate on an ALF axis system with central atom, x-axis atom, and xy-plane atom.

        :param rotation_matrix: A 3x3 rotation matrix
        """

        rot_force_dict = {}

        for atom_name, global_force in self.global_forces.items():
            rot_force_dict[atom_name] = np.matmul(
                rotation_matrix, np.array(global_force)
            )

        return rot_force_dict

    def _read_file(self):
        """Parse through a .wfn file to look for the relevant information.
        This is automatically called if an attribute is being accessed, but the
        FileState of the file is FileState.Unread"""

        atoms = Atoms()
        forces = {}

        with open(self.path, "r") as f:

            for line in f:

                if "Charge =" in line:

                    self.charge, self.multiplicity = int(line.split()[2]), int(
                        line.split()[-1]
                    )
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
                        forces[atom_name] = np.array(
                            [float(line[2]), float(line[3]), float(line[4])]
                        )
                elif "Dipole moment (field-independent basis, Debye)" in line:
                    # dipoles are on one line
                    dipole_line_split = next(f).split()
                    # every 2nd value is a dipole component
                    values = [
                        float(dipole_line_split[i])
                        for i in range(len(dipole_line_split))
                        if i % 2 != 0
                    ]
                    self.molecular_dipole = MolecularDipole(values[:3])
                elif "Quadrupole moment (field-independent basis, Debye-Ang)" in line:
                    quadrupole_lines_split = (
                        (next(f) + next(f)).replace("\n", "   ").split()
                    )
                    values = [
                        float(quadrupole_lines_split[i])
                        for i in range(len(quadrupole_lines_split))
                        if i % 2 != 0
                    ]
                    self.molecular_quadrupole = MolecularQuadrupole(*values)

                    # this is the line that says Traceless Quadrupole moment,
                    # the problem is that it contains the same text
                    # as the other quadrupole line
                    line = next(f)

                    traceless_quadrupole_lines_split = (
                        (next(f) + next(f)).replace("\n", "   ").split()
                    )
                    values = [
                        float(traceless_quadrupole_lines_split[i])
                        for i in range(len(traceless_quadrupole_lines_split))
                        if i % 2 != 0
                    ]
                    self.traceless_molecular_quadrupole = TracelessMolecularQuadrupole(
                        *values
                    )
                elif "Octapole moment (field-independent basis, Debye-Ang**2)" in line:
                    octapole_lines_split = (
                        (next(f) + next(f) + next(f)).replace("\n", "   ").split()
                    )
                    values = [
                        float(octapole_lines_split[i])
                        for i in range(len(octapole_lines_split))
                        if i % 2 != 0
                    ]
                    self.molecular_octapole = MolecularOctapole(*values)
                elif (
                    "Hexadecapole moment (field-independent basis, Debye-Ang**3)"
                    in line
                ):
                    hexadecapole_lines_split = (
                        (next(f) + next(f) + next(f) + next(f))
                        .replace("\n", "   ")
                        .split()
                    )
                    values = [
                        float(hexadecapole_lines_split[i])
                        for i in range(len(hexadecapole_lines_split))
                        if i % 2 != 0
                    ]
                    self.molecular_hexadecapole = MolecularHexadecapole(*values)

        self.global_forces = forces
        self.atoms = atoms
