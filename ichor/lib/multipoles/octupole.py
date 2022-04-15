from typing import Tuple

import numpy as np

from ichor.lib import constants


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
    o = octupole_spherical_to_cartesian(
        q30, q31c, q31s, q32c, q32s, q33c, q33s
    )
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

    return pack_cartesian_octupole(o_xxx, o_xxy, o_xxz, o_xyy, o_xyz, o_xzz, o_yyy, o_yyz, o_yzz, o_zzz)


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


def pack_cartesian_octupole(o_xxx, o_xxy, o_xxz, o_xyy, o_xyz, o_xzz, o_yyy, o_yyz, o_yzz, o_zzz):
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
    return o[0, 0, 0], o[0, 0, 1], o[0, 0, 2], o[0, 1, 1], o[0, 1, 2], o[0, 2, 2], o[1, 1, 1], o[1, 1, 2], o[1, 2, 2], o[2, 2, 2]


def octupole_rotate_cartesian(o: np.ndarray, C: np.ndarray) -> np.ndarray:
    return np.einsum("ia,jb,kc,abc->ijk", C, C, C, o)
