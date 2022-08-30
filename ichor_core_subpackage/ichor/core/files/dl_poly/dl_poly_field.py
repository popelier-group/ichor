from ichor.core.files.file import WriteFile
from typing import Union, List
from pathlib import Path
from ichor.core.calculators.geometry_calculator import get_internal_feature_indices
from ichor.core.common.constants import dlpoly_weights
from ichor.core.atoms import Atom, Atoms
from ichor.core.calculators import (
    default_connectivity_calculator,
    default_feature_calculator,
)
import numpy as np

class ConnectedAtom(Atom):
    def __init__(self, atom: Atom, parent: "ConnectedAtoms"):
        super().__init__(
            atom.type,
            atom.x,
            atom.y,
            atom.z,
            index=atom.index,
            parent=parent,
            units=atom.units,
        )
        self.bond_list = []
        self.angle_list = []
        self.dihedral_list = []

    def set_bond(self, other: Atom):
        self.bond_list += [other]

    def set_angle(self, other: Atom):
        self.angle_list += [other]

    def set_dihedral(self, other: Atom):
        self.dihedral_list += [other]

class ConnectedAtoms(Atoms):
    def __init__(self, atoms):
        super().__init__()
        for atom in atoms:
            self.add(ConnectedAtom(atom, self))

        self._bonds = []
        self._angles = []
        self._dihedrals = []

        bonds = np.array(self.connectivity(default_connectivity_calculator))
        angles = np.matmul(bonds, bonds)
        dihedrals = np.matmul(angles, bonds)

        bond_list = []
        angle_list = []
        dihedral_list = []
        
        # iterate over upper triangular matrix to avoid double counting
        for i in range(bonds.shape[0]):
            for j in range(i + 1, bonds.shape[1]):
                if bonds[i, j] == 1:
                    bond_list += [(i, j)]
                elif angles[i, j] == 1:
                    angle_list += [(i, j)]
                elif dihedrals[i, j] == 1:
                    dihedral_list += [(i, j)]

        for i, j in bond_list:
            self[i].set_bond(self[j])
            self[j].set_bond(self[i])
            self._bonds.append((i, j))

        for i, j in angle_list:
            for k in list(set(self[i].bond_list) & set(self[j].bond_list)):
                self[i].set_angle(self[j])
                self[j].set_angle(self[i])
                self._angles.append((i, k.i, j))

        for i, j in dihedral_list:
            iatoms = list(set(self[i].bond_list) & set(self[j].angle_list))
            jatoms = list(set(self[j].bond_list) & set(self[i].angle_list))
            for k in iatoms:
                for l in jatoms:
                    if k in self[l.i].bond_list:
                        self[i].set_dihedral(self[j])
                        self[j].set_dihedral(self[i])
                        self._dihedrals.append((i, k.i, l.i, j))
                        break

    @property
    def bonds(self):
        return [(i + 1, j + 1) for i, j in self._bonds]

    @property
    def angles(self):
        return [(i + 1, j + 1, k + 1) for i, j, k in self._angles]

    @property
    def dihedrals(self):
        return [(i + 1, j + 1, k + 1, l + 1) for i, j, k, l in self._dihedrals]

    def bond_names(self) -> List[str]:
        return [f"{self[i].name}-{self[j].name}" for i, j in self._bonds]

    def angle_names(self) -> List[str]:
        return [
            f"{self[i].name}-{self[j].name}-{self[k].name}"
            for i, j, k in self._angles
        ]

    def dihedral_names(self) -> List[str]:
        return [
            f"{self[i].name}-{self[j].name}-{self[k].name}-{self[l].name}"
            for i, j, k, l in self._dihedrals
        ]

    def names(self):
        return (
            self.bond_names(),
            self.angle_names(),
            self.dihedral_names(),
        )

class DlPolyField(WriteFile):
    
    def __init__(self, path: Union[Path, str],
                 atoms,
                 system_name: str,
                 nummols = 1,
                 
                 
                 ):
        super().__init__(path)
        
        self.atoms = atoms
        self.system_name = system_name
        self.nummols = nummols

    # TODO: implement reading for dlpoly field file
    # def _read_file(self):
    #     ...

    def _write_file(self, path: Path):

        bonds, angles, dihedrals = get_internal_feature_indices(self.atoms)

        with open(path, "w") as f:
            f.write("DL_FIELD v3.00\n")
            f.write("Units kJ/mol\n")
            f.write("Molecular types 1\n")
            f.write(f"{self.system_name}\n")
            f.write(f"nummols {self.nummols}\n")
            f.write(f"atoms {len(self.atoms)}\n")
            for atom in self.atoms:
                f.write(
                    #  Atom Type      Atomic Mass                    Charge Repeats Frozen(0=NotFrozen)
                    f"{atom.type}\t\t{dlpoly_weights[atom.type]:.7f}     0.0   1   0\n"
                )
            f.write(f"BONDS {len(bonds)}\n")
            for i, j in bonds:
                f.write(f"harm {i} {j} 0.0 0.0\n")
            if len(angles) > 0:
                f.write(f"ANGLES {len(angles)}\n")
                for i, j, k in angles:
                    f.write(f"harm {i} {j} {k} 0.0 0.0\n")
            if len(dihedrals) > 0:
                f.write(f"DIHEDRALS {len(dihedrals)}\n")
                for i, j, k, l in dihedrals:
                    f.write(f"harm {i} {j} {k} {l} 0.0 0.0\n")
            f.write("finish\n")
            f.write("close\n")