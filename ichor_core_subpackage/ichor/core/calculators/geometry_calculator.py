from typing import List, Tuple

import numpy as np
from ichor.core.common.linalg import mag

def calculate_bond(atoms: "Atoms", i: int, j: int):
    """
    Calculates the bond distance between atoms i and j for atoms
    :param atoms: instance of 'Atoms' to calculate bond distance
    :param i: 0-index atoms[i]
    :param j: 0-index atoms[j]
    :return: bond distance between atoms i-j as float
    """
    return atoms[i].dist(atoms[j])


def calculate_bonds(atoms: "Atoms") -> np.ndarray:
    connected_atoms = get_connected_atoms(atoms)
    return np.array(
        [calculate_bond(atoms, i, j) for i, j in connected_atoms._bonds]
    )


def calculate_angle(atoms: "Atoms", i: int, j: int, k: int):
    """
    Calculates the angle between atoms i, j, and k for atoms
    :param atoms: instance of 'Atoms' to calculate angle
    :param i: 0-index atoms[i]
    :param j: 0-index atoms[j]
    :param k: 0-index atoms[k]
    :return: angle between atoms i-j-k as float
    """
    return np.degrees(atoms[j].angle(atoms[i], atoms[k]))


def calculate_angles(atoms: "Atoms") -> np.ndarray:
    connected_atoms = get_connected_atoms(atoms)
    return np.array(
        [
            calculate_angle(atoms, i, j, k)
            for i, j, k in connected_atoms._angles
        ]
    )


def calculate_dihedral(atoms: "Atoms", i: int, j: int, k: int, l: int) -> float:
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


def calculate_dihedrals(atoms: "Atoms") -> np.ndarray:
    connected_atoms = get_connected_atoms(atoms)
    return np.array(
        [
            calculate_dihedral(atoms, i, j, k, l)
            for i, j, k, l in connected_atoms._dihedrals
        ]
    )


def get_connected_atoms(atoms: "Atoms") -> "ConnectedAtoms":
    
    from ichor.core.files.dl_poly.dl_poly_field import ConnectedAtoms

    connected_atoms = ConnectedAtoms(atoms)
    return connected_atoms


def bond_names(atoms: "Atoms") -> List[str]:
    """
    Returns the bond names for atoms
    :param atoms: 'Atoms' instance to get the bond names
    :return: bond names of atoms as list of str
    """
    return get_connected_atoms(atoms).bond_names()


def angle_names(atoms: "Atoms") -> List[str]:
    """
    Returns the angle names for atoms
    :param atoms: 'Atoms' instance to get the angle names
    :return: angle names of atoms as list of str
    """
    return get_connected_atoms(atoms).angle_names()


def dihedral_names(atoms: "Atoms") -> List[str]:
    """
    Returns the dihedral names for atoms
    :param atoms: 'Atoms' instance to get the dihedral names
    :return: dihedral names of atoms as list of str
    """
    return get_connected_atoms(atoms).dihedral_names()


def internal_feature_names(
    atoms: "Atoms",
) -> Tuple[List[str], List[str], List[str]]:
    """
    Gets the names of the bonds, angles and dihedrals for atoms
    :param atoms: instance of 'Atoms' to get the names for bonds, angles and dihedrals
    :return: tuple of lists of the names for the bonds angles and dihedrals for atoms
    """
    return bond_names(atoms), angle_names(atoms), dihedral_names(atoms)


def calculate_internal_features(
    atoms: "Atoms",
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


def bonds(atoms: "Atoms") -> List[Tuple[int, int]]:
    return get_connected_atoms(atoms).bonds


def angles(atoms: "Atoms") -> List[Tuple[int, int, int]]:
    return get_connected_atoms(atoms).angles


def dihedrals(atoms: "Atoms") -> List[Tuple[int, int, int, int]]:
    return get_connected_atoms(atoms).dihedrals


def get_internal_feature_indices(
    atoms: "Atoms",
) -> Tuple[
    List[Tuple[int, int]],
    List[Tuple[int, int, int]],
    List[Tuple[int, int, int, int]],
]:
    return bonds(atoms), angles(atoms), dihedrals(atoms)
