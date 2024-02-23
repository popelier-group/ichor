from typing import Tuple

import numpy as np
from ichor.core.common import constants


def rotate_octupole(
    q30: float,
    q31c: float,
    q31s: float,
    q32c: float,
    q32s: float,
    q33c: float,
    q33s: float,
    C: np.ndarray,
) -> Tuple[float, float, float, float, float, float, float]:
    """Rotates octupole moments from the global to local frame"""

    # transform global spherical tensor to global cartesian tensor
    o = octupole_spherical_to_cartesian(q30, q31c, q31s, q32c, q32s, q33c, q33s)
    # rotate global cartesian to local cartesian frame
    rotated_o = octupole_rotate_cartesian(o, C)

    # transform local cartesian to local spherical tensor
    return octupole_cartesian_to_spherical(rotated_o)


def octupole_spherical_to_cartesian(
    q30: float,
    q31c: float,
    q31s: float,
    q32c: float,
    q32s: float,
    q33c: float,
    q33s: float,
) -> np.ndarray:
    o_xxx = constants.rt5_8 * q33c - constants.rt3_8 * q31c
    o_xxy = constants.rt5_8 * q33s - constants.rt1_24 * q31s
    o_xxz = constants.rt5_12 * q32c - 0.5 * q30
    o_xyy = -(constants.rt5_8 * q33c + constants.rt1_24 * q31c)
    o_xyz = constants.rt5_12 * q32s
    o_xzz = constants.rt2_3 * q31c
    o_yyy = -(constants.rt5_8 * q33s + constants.rt3_8 * q31s)
    o_yyz = -(constants.rt5_12 * q32c + 0.5 * q30)
    o_yzz = constants.rt2_3 * q31s
    o_zzz = q30

    return pack_cartesian_octupole(
        o_xxx, o_xxy, o_xxz, o_xyy, o_xyz, o_xzz, o_yyy, o_yyz, o_yzz, o_zzz
    )


def octupole_cartesian_to_spherical(
    o: np.ndarray,
) -> Tuple[float, float, float, float, float, float, float]:
    q30 = o[2, 2, 2]
    q31c = constants.rt3_2 * o[0, 2, 2]
    q31s = constants.rt3_2 * o[1, 2, 2]
    q32c = constants.rt_3_5 * (o[0, 0, 2] - o[1, 1, 2])
    q32s = 2 * constants.rt_3_5 * o[0, 1, 2]
    q33c = constants.rt_1_10 * (o[0, 0, 0] - 3 * o[0, 1, 1])
    q33s = constants.rt_1_10 * (3 * o[0, 0, 1] - o[1, 1, 1])
    return q30, q31c, q31s, q32c, q32s, q33c, q33s


def pack_cartesian_octupole(
    o_xxx, o_xxy, o_xxz, o_xyy, o_xyz, o_xzz, o_yyy, o_yyz, o_yzz, o_zzz
):
    return np.array(
        [
            [
                [o_xxx, o_xxy, o_xxz],
                [o_xxy, o_xyy, o_xyz],
                [o_xxz, o_xyz, o_xzz],
            ],
            [
                [o_xxy, o_xyy, o_xyz],
                [o_xyy, o_yyy, o_yyz],
                [o_xyz, o_yyz, o_yzz],
            ],
            [
                [o_xxz, o_xyz, o_xzz],
                [o_xyz, o_yyz, o_yzz],
                [o_xzz, o_yzz, o_zzz],
            ],
        ]
    )


def unpack_cartesian_octupole(o):
    return (
        o[0, 0, 0],
        o[0, 0, 1],
        o[0, 0, 2],
        o[0, 1, 1],
        o[0, 1, 2],
        o[0, 2, 2],
        o[1, 1, 1],
        o[1, 1, 2],
        o[1, 2, 2],
        o[2, 2, 2],
    )


def octupole_rotate_cartesian(o: np.ndarray, C: np.ndarray) -> np.ndarray:
    return np.einsum("ia,jb,kc,abc->ijk", C, C, C, o)


def q30_prime(q30, q00, q10, q11c, q11s, q20, q21s, q21c, atomic_coordinates):

    x, y, z = atomic_coordinates
    norm_sq = np.sum(atomic_coordinates**2)

    return (
        q30
        + (1.5 * (3 * z**2 - norm_sq) * q10)
        - (constants.rt3 * x * q21c)
        - (constants.rt3 * y * q21s)
        + (3 * z * q20)
        + ((z / 2.0) * ((5 * z**2) - (3 * norm_sq)) * q00)
        - (3 * x * z * q11c)
        - (3 * y * z * q11s)
    )


def q32s_prime(q32s, q00, q10, q11c, q11s, q21s, q21c, q22s, atomic_coordinates):

    x, y, z = atomic_coordinates
    norm_sq = np.sum(atomic_coordinates**2)

    return (
        q32s
        + (constants.rt_3_5 * ((5 * x * y * z) - norm_sq) * q00)
        + (constants.rt_3_5 * ((5 * y * z) - 2 * x) * q11c)
        + (constants.rt_3_5 * ((5 * x * z) - 2 * y) * q11s)
        + (constants.rt_3_5 * ((5 * x * y) - 2 * z) * q10)
        + (constants.rt5 * z * q22s)
        + (constants.rt5 * y * q21c)
        + (constants.rt5 * x * q21s)
    )


def atomic_contribution_to_molecular_octupole(
    q00, q10, q11s, q11c, q20, q21c, q21s, q22c, q22s, q30, q32s, atomic_coordinates
):

    q30_pr = q30_prime(q30, q00, q10, q11s, q11c, q20, q21c, q21s, atomic_coordinates)
    q32_pr = q32s_prime(
        q32s, q00, q10, q11c, q11s, q21s, q21c, q22s, atomic_coordinates
    )

    return np.array([q30_pr, q32_pr])


def recover_molecular_octupole(
    atoms: "Atoms",  # noqa
    ints_dir: "IntDirectory",  # noqa
    atoms_in_angstroms=True,
    convert_to_debye_angstrom_squared=True,
    convert_to_cartesian=True,
    unpack=True,
    include_prefactor=True,
):

    # make sure we are in Bohr
    if atoms_in_angstroms:
        atoms = atoms.to_bohr()

    # TODO: implement rest of octupole conversions
    # spherical representation
    # molecular_octupole = np.zeros(7)

    tmp_arr = np.zeros(2)

    for atom in atoms:

        # get necessary data for calculations
        atom_coords = atom.coordinates
        global_multipoles = ints_dir[atom.name].global_multipole_moments

        # get the values for a particular atom
        q00 = global_multipoles["q00"]
        q10 = global_multipoles["q10"]
        q11c = global_multipoles["q11c"]
        q11s = global_multipoles["q11s"]
        q20 = global_multipoles["q20"]
        q21c = global_multipoles["q21c"]
        q21s = global_multipoles["q21s"]
        q22c = global_multipoles["q22c"]
        q22s = global_multipoles["q22s"]
        q30 = global_multipoles["q30"]
        q32s = global_multipoles["q32s"]

        tmp_arr += atomic_contribution_to_molecular_octupole(
            q00, q10, q11c, q11s, q20, q21c, q21s, q22c, q22s, q30, q32s, atom_coords
        )

    return tmp_arr
