from typing import Tuple

import numpy as np
from ichor.core.common import constants


# Discussion of traceless tensors https://ocw.mit.edu/courses/8-07-electromagnetism-ii-fall-2012/pages/lecture-notes/
# https://ocw.mit.edu/courses/8-07-electromagnetism-ii-fall-2012/resources/mit8_07f12_ln9/
# equation 9.39


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


def octupole_element_conversion(octupole_array: np.ndarray, current_ordering):
    """Converts between the two ways of reporting octupole moments, namely

      0: XXX, YYY, ZZZ, XYY, XXY, XXZ, XZZ, YZZ, YYZ, XYZ
      and
      1: XXX, XXY, XXZ, XYY, XYZ, XZZ, YYY, YYZ, YZZ, ZZZ

      where the 0 and 1 indicate the ordering index. The other ordering is going to be returned

    :param octupole_array: 1d unpacked octupole array
    :type ordering: either 0 or 1
    """

    if current_ordering == 0:
        return octupole_array[[0, 4, 5, 3, 9, 6, 1, 8, 7, 2]]

    elif current_ordering == 1:
        return octupole_array[[0, 6, 9, 3, 1, 2, 5, 8, 7, 4]]

    raise ValueError(
        f"Current ordering can be either 0 or 1, but it is {current_ordering}"
    )


def octupole_rotate_cartesian(o: np.ndarray, C: np.ndarray) -> np.ndarray:
    return np.einsum("ia,jb,kc,abc->ijk", C, C, C, o)


def q30_prime(q30, q00, q10, q11c, q11s, q20, q21c, q21s, atomic_coordinates):

    x, y, z = atomic_coordinates
    norm_sq = np.sum(atomic_coordinates**2)

    return (
        q30
        + (1.5 * ((3 * z**2) - norm_sq) * q10)
        - (constants.rt3 * x * q21c)
        - (constants.rt3 * y * q21s)
        + (3 * z * q20)
        + ((z / 2.0) * ((5 * z**2) - (3 * norm_sq)) * q00)
        - (3 * x * z * q11c)
        - (3 * y * z * q11s)
    )


def q32s_prime(q32s, q00, q10, q11c, q11s, q21c, q21s, q22s, atomic_coordinates):

    x, y, z = atomic_coordinates

    return (
        q32s
        + constants.rt5 * (z * q22s + y * q21c + x * q21s)
        + constants.rt15 * (z * y * q11c + x * z * q11s + y * x * q10)
        + constants.rt15 * (x * y * z * q00)
    )


def atomic_contribution_to_molecular_octupole(
    q00, q10, q11c, q11s, q20, q21c, q21s, q22c, q22s, q30, q32s, atomic_coordinates
):

    q30_pr = q30_prime(q30, q00, q10, q11c, q11s, q20, q21c, q21s, atomic_coordinates)
    q32s_pr = q32s_prime(
        q32s, q00, q10, q11c, q11s, q21c, q21s, q22s, atomic_coordinates
    )

    return np.array([q30_pr, q32s_pr])


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

    # from anthony stone theory of intermolecular forces p21-22
    prefactor = 2.5

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

    if convert_to_debye_angstrom_squared:
        tmp_arr *= constants.coulom_bohr_cubed_to_debye_angstrom_squared

    if convert_to_cartesian:
        tmp_arr = octupole_spherical_to_cartesian(
            tmp_arr[0], 0.0, 0.0, 0.0, tmp_arr[1], 0.0, 0.0
        )

        if unpack:
            tmp_arr = np.array(unpack_cartesian_octupole(tmp_arr))
            # convert from XXX, XXY, XXZ, XYY, XYZ, XZZ, YYY, YYZ, YZZ, ZZZ
            # to XXX, YYY, ZZZ, XYY, XXY, XXZ, XZZ, YZZ, YYZ, XYZ
            tmp_arr = octupole_element_conversion(tmp_arr, 1)

    if include_prefactor:
        tmp_arr = prefactor * tmp_arr

    return tmp_arr
