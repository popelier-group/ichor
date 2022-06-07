from typing import Tuple

import numpy as np

from ichor.core import constants


def rotate_quadrupole(
    q20: float,
    q21c: float,
    q21s: float,
    q22c: float,
    q22s: float,
    C: np.ndarray,
) -> Tuple[float, float, float, float, float]:
    """Rotates quadrupole moments from the global to local frame"""
    # transform global spherical tensor to global cartesian tensor
    q = quadrupole_spherical_to_cartesian(q20, q21c, q21s, q22c, q22s)
    # rotate global cartesian to local cartesian frame
    rotated_q = quadrupole_rotate_cartesian(q, C)
    # transform local cartesian to local spherical tensor
    return quadrupole_cartesian_to_spherical(rotated_q)


def quadrupole_spherical_to_cartesian(
    q20, q21c, q21s, q22c, q22s
) -> np.ndarray:
    q_xx = 0.5 * (constants.rt3 * q22c - q20)
    q_xy = 0.5 * constants.rt3 * q22s
    q_xz = 0.5 * constants.rt3 * q21c
    q_yy = -0.5 * (constants.rt3 * q22c + q20)
    q_yz = 0.5 * constants.rt3 * q21s
    q_zz = q20

    return pack_cartesian_quadrupole(q_xx, q_xy, q_xz, q_yy, q_yz, q_zz)


def quadrupole_cartesian_to_spherical(
    q: np.ndarray,
) -> Tuple[float, float, float, float, float]:
    q20 = q[2, 2]
    q21c = 2 / constants.rt3 * q[0, 2]
    q21s = constants.rt12_3 * q[1, 2]
    q22c = 1 / constants.rt3 * (q[0, 0] - q[1, 1])
    q22s = 2 / constants.rt3 * q[0, 1]
    return q20, q21c, q21s, q22c, q22s


def pack_cartesian_quadrupole(q_xx, q_xy, q_xz, q_yy, q_yz, q_zz):
    return np.array(
        [[q_xx, q_xy, q_xz], [q_xy, q_yy, q_yz], [q_xz, q_yz, q_zz]]
    )


def unpack_cartesian_quadrupole(q):
    return q[0, 0], q[0, 1], q[0, 2], q[1, 1], q[1, 2], q[2, 2]


def quadrupole_rotate_cartesian(q: np.ndarray, C: np.ndarray) -> np.ndarray:
    return np.einsum("ia,jb,ab->ij", C, C, q)
