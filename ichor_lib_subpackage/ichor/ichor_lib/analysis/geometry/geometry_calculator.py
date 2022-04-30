from typing import List, Tuple

import numpy as np

from ichor.ichor_lib.atoms import Atom, Atoms
from ichor.ichor_lib.common.linalg import mag


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

        bonds = np.array(self.connectivity)
        angles = np.matmul(bonds, bonds)
        dihedrals = np.matmul(angles, bonds)

        bond_list = []
        angle_list = []
        dihedral_list = []
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


_connected_atoms = {}


def calculate_bond(atoms: Atoms, i: int, j: int):
    """
    Calculates the bond distance between atoms i and j for atoms
    :param atoms: instance of 'Atoms' to calculate bond distance
    :param i: 0-index atoms[i]
    :param j: 0-index atoms[j]
    :return: bond distance between atoms i-j as float
    """
    return atoms[i].dist(atoms[j])


def calculate_bonds(atoms: Atoms) -> np.ndarray:
    connected_atoms = get_connected_atoms(atoms)
    return np.array(
        [calculate_bond(atoms, i, j) for i, j in connected_atoms._bonds]
    )


def calculate_angle(atoms: Atoms, i: int, j: int, k: int):
    """
    Calculates the angle between atoms i, j, and k for atoms
    :param atoms: instance of 'Atoms' to calculate angle
    :param i: 0-index atoms[i]
    :param j: 0-index atoms[j]
    :param k: 0-index atoms[k]
    :return: angle between atoms i-j-k as float
    """
    return np.degrees(atoms[j].angle(atoms[i], atoms[k]))


def calculate_angles(atoms: Atoms) -> np.ndarray:
    connected_atoms = get_connected_atoms(atoms)
    return np.array(
        [
            calculate_angle(atoms, i, j, k)
            for i, j, k in connected_atoms._angles
        ]
    )


def calculate_dihedral(atoms: Atoms, i: int, j: int, k: int, l: int) -> float:
    """
    Calculates the dihedral angle between atoms i, j, k and l for atoms
    :param atoms: instance of 'Atoms' to calculate dihedral angle
    :param i: 0-index atoms[i]
    :param j: 0-index atoms[j]
    :param k: 0-index atoms[k]
    :param l: 0-index atoms[l]
    :return: dihedral angle between atoms i-j-k-l as float
    """
    b1 = np.array(atoms[j].vec_to(atoms[i]))
    b2 = np.array(atoms[k].vec_to(atoms[j]))
    b3 = np.array(atoms[l].vec_to(atoms[k]))

    v1 = np.cross(b1, b2)
    v2 = np.cross(b2, b3)

    n1 = v1 / mag(v1)
    n2 = v2 / mag(v2)

    m1 = np.cross(n1, b2 / np.linalg.norm(b2))

    x = np.dot(n1, n2)
    y = np.dot(m1, n2)

    return (
        np.degrees(np.arctan2(y, x)) + 180
    ) % 360  # - 180 # <- Uncomment to get angle from -180 to +180


def calculate_dihedrals(atoms: Atoms) -> np.ndarray:
    connected_atoms = get_connected_atoms(atoms)
    return np.array(
        [
            calculate_dihedral(atoms, i, j, k, l)
            for i, j, k, l in connected_atoms._dihedrals
        ]
    )


def get_connected_atoms(atoms: Atoms) -> ConnectedAtoms:
    if atoms.hash not in _connected_atoms.keys():
        _connected_atoms[atoms.hash] = ConnectedAtoms(atoms)
    return _connected_atoms[atoms.hash]


def bond_names(atoms: Atoms) -> List[str]:
    """
    Returns the bond names for atoms
    :param atoms: 'Atoms' instance to get the bond names
    :return: bond names of atoms as list of str
    """
    return get_connected_atoms(atoms).bond_names()


def angle_names(atoms: Atoms) -> List[str]:
    """
    Returns the angle names for atoms
    :param atoms: 'Atoms' instance to get the angle names
    :return: angle names of atoms as list of str
    """
    return get_connected_atoms(atoms).angle_names()


def dihedral_names(atoms: Atoms) -> List[str]:
    """
    Returns the dihedral names for atoms
    :param atoms: 'Atoms' instance to get the dihedral names
    :return: dihedral names of atoms as list of str
    """
    return get_connected_atoms(atoms).dihedral_names()


def internal_feature_names(
    atoms: Atoms,
) -> Tuple[List[str], List[str], List[str]]:
    """
    Gets the names of the bonds, angles and dihedrals for atoms
    :param atoms: instance of 'Atoms' to get the names for bonds, angles and dihedrals
    :return: tuple of lists of the names for the bonds angles and dihedrals for atoms
    """
    return bond_names(atoms), angle_names(atoms), dihedral_names(atoms)


def calculate_internal_features(
    atoms,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculates the bonds, angles and dihedrals for atoms
    :param atoms: instance of `Atoms` to calculate the bonds, angles and dihedrals for
    :return: bonds, angles and dihedrals as a tuple of numpy arrays
    """
    return (
        calculate_bonds(atoms),
        calculate_angles(atoms),
        calculate_dihedrals(atoms),
    )


def bonds(atoms: Atoms) -> List[Tuple[int, int]]:
    return get_connected_atoms(atoms).bonds


def angles(atoms: Atoms) -> List[Tuple[int, int, int]]:
    return get_connected_atoms(atoms).angles


def dihedrals(atoms: Atoms) -> List[Tuple[int, int, int, int]]:
    return get_connected_atoms(atoms).dihedrals


def get_internal_feature_indices(
    atoms,
) -> Tuple[
    List[Tuple[int, int]],
    List[Tuple[int, int, int]],
    List[Tuple[int, int, int, int]],
]:
    return bonds(atoms), angles(atoms), dihedrals(atoms)
