from typing import Tuple

import numpy as np


def rotate_dipole(
    q10: float, q11c: float, q11s: float, C: np.ndarray
) -> Tuple[float, float, float]:
    """Rotates dipole moment from global cartesian to local cartesian.

    :param q10: q10 component
    :param q11c: q11c component
    :param q11s: q11s component
    :param C: C matrix to use to rotate dipoles
    """

    # Global cartesian dipole moment d is a simple rearrangement of the spherical form
    d = dipole_spherical_to_cartesian(q10, q11c, q11s)
    # Rotation of 1D cartesian tensor from global to local frame
    rotated_d = dipole_rotate_cartesian(d, C)
    # Convert Local Cartesian to Local Spherical
    return dipole_cartesian_to_spherical(rotated_d)


def dipole_spherical_to_cartesian(q10, q11c, q11s) -> np.ndarray:
    return np.array([q11c, q11s, q10])


def dipole_cartesian_to_spherical(d: np.ndarray) -> Tuple[float, float, float]:
    return d[2], d[0], d[1]


def pack_cartesian_dipole(d_x, d_y, d_z):
    return np.array([d_x, d_y, d_z])


def unpack_cartesian_dipole(d):
    return d[0], d[1], d[2]


def dipole_rotate_cartesian(d: np.ndarray, C: np.ndarray) -> np.ndarray:
    return np.einsum("ia,a->i", C, d)
