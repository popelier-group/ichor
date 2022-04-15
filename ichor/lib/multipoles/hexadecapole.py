from typing import Tuple

import numpy as np

from ichor.lib import constants


def rotate_hexadecapole(
    q40: float,
    q41c: float,
    q41s: float,
    q42c: float,
    q42s: float,
    q43c: float,
    q43s: float,
    q44c: float,
    q44s: float,
    C: np.ndarray,
) -> Tuple[float, float, float, float, float, float, float, float, float]:
    """Rotates hexadecapole moments from the global to local frame"""
    # transform global spherical tensor to global cartesian tensor
    h = hexadecapole_spherical_to_cartesian(
        q40, q41c, q41s, q42c, q42s, q43c, q43s, q44c, q44s
    )
    # rotate global cartesian to local cartesian frame
    h_rotated = hexadecapole_rotate_cartesian(h, C)
    # transform local cartesian to local spherical tensor
    return hexadecapole_cartesian_to_spherical(h_rotated)


def hexadecapole_spherical_to_cartesian(
    q40: float,
    q41c: float,
    q41s: float,
    q42c: float,
    q42s: float,
    q43c: float,
    q43s: float,
    q44c: float,
    q44s: float,
) -> np.ndarray:
    h_xxxx = (
        0.375 * q40
        - 0.25 * constants.rt5 * q42c
        + 0.125 * constants.rt35 * q44c
    )
    h_xxxy = 0.125 * (constants.rt35 * q44s - constants.rt5 * q42s)
    h_xxxz = 0.0625 * (constants.rt70 * q43c - 3.0 * constants.rt10 * q41c)
    h_xxyy = 0.125 * q40 - 0.125 * constants.rt35 * q44c
    h_xxyz = 0.0625 * (constants.rt70 * q43s - constants.rt10 * q41s)
    h_xxzz = 0.5 * (0.5 * constants.rt5 * q42c - q40)
    h_xyyy = -0.125 * (constants.rt5 * q42s + constants.rt35 * q44s)
    h_xyyz = -0.0625 * (constants.rt10 * q41c + constants.rt70 * q43c)
    h_xyzz = 0.25 * constants.rt5 * q42s
    h_xzzz = constants.rt5_8 * q41c
    h_yyyy = (
        0.375 * q40
        + 0.25 * constants.rt5 * q42c
        + 0.125 * constants.rt35 * q44c
    )
    h_yyyz = -0.0625 * (3.0 * constants.rt10 * q41s + constants.rt70 * q43s)
    h_yyzz = -0.5 * (0.5 * constants.rt5 * q42c + q40)
    h_yzzz = constants.rt5_8 * q41s
    h_zzzz = q40

    return pack_cartesian_hexadecapole(h_xxxx, h_xxxy, h_xxxz, h_xxyy, h_xxyz, h_xxzz, h_xyyy, h_xyyz, h_xyzz, h_xzzz, h_yyyy, h_yyyz, h_yyzz, h_yzzz, h_zzzz)


def hexadecapole_cartesian_to_spherical(
    h: np.ndarray,
) -> Tuple[float, float, float, float, float, float, float, float, float]:
    q40 = h[2, 2, 2, 2]
    q41c = constants.rt_8_5 * h[0, 2, 2, 2]
    q41s = constants.rt_8_5 * h[1, 2, 2, 2]
    q42c = 2 * constants.rt_1_5 * (h[0, 0, 2, 2] - h[1, 1, 2, 2])
    q42s = 4 * constants.rt_1_5 * h[0, 1, 2, 2]
    q43c = 2 * constants.rt_2_35 * (h[0, 0, 0, 2] - 3 * h[0, 1, 1, 2])
    q43s = 2 * constants.rt_2_35 * (3 * h[0, 0, 1, 2] - h[1, 1, 1, 2])
    q44c = constants.rt_1_35 * (
        h[0, 0, 0, 0] - 6 * h[0, 0, 1, 1] + h[1, 1, 1, 1]
    )
    q44s = 4 * constants.rt_1_35 * (h[0, 0, 0, 1] - h[0, 1, 1, 1])
    return q40, q41c, q41s, q42c, q42s, q43c, q43s, q44c, q44s


def pack_cartesian_hexadecapole(h_xxxx, h_xxxy, h_xxxz, h_xxyy, h_xxyz, h_xxzz, h_xyyy, h_xyyz, h_xyzz, h_xzzz, h_yyyy, h_yyyz, h_yyzz, h_yzzz, h_zzzz):
    return np.array(
        [
            [
                [
                    [h_xxxx, h_xxxy, h_xxxz],
                    [h_xxxy, h_xxyy, h_xxyz],
                    [h_xxxz, h_xxyz, h_xxzz],
                ],
                [
                    [h_xxxy, h_xxyy, h_xxyz],
                    [h_xxyy, h_xyyy, h_xyyz],
                    [h_xxyz, h_xyyz, h_xyzz],
                ],
                [
                    [h_xxxz, h_xxyz, h_xxzz],
                    [h_xxyz, h_xyyz, h_xyzz],
                    [h_xxzz, h_xyzz, h_xzzz],
                ],
            ],
            [
                [
                    [h_xxxy, h_xxyy, h_xxyz],
                    [h_xxyy, h_xyyy, h_xyyz],
                    [h_xxyz, h_xyyz, h_xyzz],
                ],
                [
                    [h_xxyy, h_xyyy, h_xyyz],
                    [h_xyyy, h_yyyy, h_yyyz],
                    [h_xyyz, h_yyyz, h_yyzz],
                ],
                [
                    [h_xxyz, h_xyyz, h_xyzz],
                    [h_xyyz, h_yyyz, h_yyzz],
                    [h_xyzz, h_yyzz, h_yzzz],
                ],
            ],
            [
                [
                    [h_xxxz, h_xxyz, h_xxzz],
                    [h_xxyz, h_xyyz, h_xyzz],
                    [h_xxzz, h_xyzz, h_xzzz],
                ],
                [
                    [h_xxyz, h_xyyz, h_xyzz],
                    [h_xyyz, h_yyyz, h_yyzz],
                    [h_xyzz, h_yyzz, h_yzzz],
                ],
                [
                    [h_xxzz, h_xyzz, h_xzzz],
                    [h_xyzz, h_yyzz, h_yzzz],
                    [h_xzzz, h_yzzz, h_zzzz],
                ],
            ],
        ]
    )


def unpack_cartesian_hexadecapole(h):
    # h_xxxx, h_xxxy, h_xxxz, h_xxyy, h_xxyz, h_xxzz, h_xyyy, h_xyyz, h_xyzz, h_xzzz, h_yyyy, h_yyyz, h_yyzz, h_yzzz, h_zzzz
    return h[0, 0, 0, 0], h[0, 0, 0, 1], h[0, 0, 0, 2], h[0, 0, 1, 1], h[0, 0, 1, 2], h[0, 0, 2, 2], h[0, 1, 1, 1], h[0, 1, 1, 2], h[0, 1, 2, 2], h[0, 2, 2, 2], h[1, 1, 1, 1], h[1, 1, 1, 2], h[1, 1, 2, 2], h[1, 2, 2, 2], h[2, 2, 2, 2]


def hexadecapole_rotate_cartesian(h: np.ndarray, C: np.ndarray) -> np.ndarray:
    return np.einsum("ia,jb,kc,ld,abcd->ijkl", C, C, C, C, h)
