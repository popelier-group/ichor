from typing import Tuple

import numpy as np
from ichor.core.common import constants
from ichor.core.common.arith import kronecker_delta


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
    h_xxxx = 0.375 * q40 - 0.25 * constants.rt5 * q42c + 0.125 * constants.rt35 * q44c
    h_xxxy = 0.125 * (constants.rt35 * q44s - constants.rt5 * q42s)
    h_xxxz = 0.0625 * (constants.rt70 * q43c - 3.0 * constants.rt10 * q41c)
    h_xxyy = 0.125 * q40 - 0.125 * constants.rt35 * q44c
    h_xxyz = 0.0625 * (constants.rt70 * q43s - constants.rt10 * q41s)
    h_xxzz = 0.5 * (0.5 * constants.rt5 * q42c - q40)
    h_xyyy = -0.125 * (constants.rt5 * q42s + constants.rt35 * q44s)
    h_xyyz = -0.0625 * (constants.rt10 * q41c + constants.rt70 * q43c)
    h_xyzz = 0.25 * constants.rt5 * q42s
    h_xzzz = constants.rt5_8 * q41c
    h_yyyy = 0.375 * q40 + 0.25 * constants.rt5 * q42c + 0.125 * constants.rt35 * q44c
    h_yyyz = -0.0625 * (3.0 * constants.rt10 * q41s + constants.rt70 * q43s)
    h_yyzz = -0.5 * (0.5 * constants.rt5 * q42c + q40)
    h_yzzz = constants.rt5_8 * q41s
    h_zzzz = q40

    return pack_cartesian_hexadecapole(
        h_xxxx,
        h_xxxy,
        h_xxxz,
        h_xxyy,
        h_xxyz,
        h_xxzz,
        h_xyyy,
        h_xyyz,
        h_xyzz,
        h_xzzz,
        h_yyyy,
        h_yyyz,
        h_yyzz,
        h_yzzz,
        h_zzzz,
    )


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
    q44c = constants.rt_1_35 * (h[0, 0, 0, 0] - 6 * h[0, 0, 1, 1] + h[1, 1, 1, 1])
    q44s = 4 * constants.rt_1_35 * (h[0, 0, 0, 1] - h[0, 1, 1, 1])
    return q40, q41c, q41s, q42c, q42s, q43c, q43s, q44c, q44s


def pack_cartesian_hexadecapole(
    h_xxxx,
    h_xxxy,
    h_xxxz,
    h_xxyy,
    h_xxyz,
    h_xxzz,
    h_xyyy,
    h_xyyz,
    h_xyzz,
    h_xzzz,
    h_yyyy,
    h_yyyz,
    h_yyzz,
    h_yzzz,
    h_zzzz,
):
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
    # h_xxxx, h_xxxy, h_xxxz, h_xxyy, h_xxyz, h_xxzz, h_xyyy,
    # h_xyyz, h_xyzz, h_xzzz, h_yyyy, h_yyyz, h_yyzz, h_yzzz, h_zzzz
    return (
        h[0, 0, 0, 0],
        h[0, 0, 0, 1],
        h[0, 0, 0, 2],
        h[0, 0, 1, 1],
        h[0, 0, 1, 2],
        h[0, 0, 2, 2],
        h[0, 1, 1, 1],
        h[0, 1, 1, 2],
        h[0, 1, 2, 2],
        h[0, 2, 2, 2],
        h[1, 1, 1, 1],
        h[1, 1, 1, 2],
        h[1, 1, 2, 2],
        h[1, 2, 2, 2],
        h[2, 2, 2, 2],
    )


def hexadecapole_rotate_cartesian(h: np.ndarray, C: np.ndarray) -> np.ndarray:
    return np.einsum("ia,jb,kc,ld,abcd->ijkl", C, C, C, C, h)


def mu_prime(alpha, displacement_vector):

    return displacement_vector[alpha]


def theta_prime(alpha, beta, displacement_vector):

    norm = np.linalg.norm(displacement_vector)
    displacement_alpha = displacement_vector[alpha]
    displacement_beta = displacement_vector[beta]

    return 0.5 * (
        3 * displacement_alpha * displacement_beta
        - norm**2 * kronecker_delta(alpha, beta)
    )


def omega_prime(alpha, beta, gamma, displacement_vector):

    norm = np.linalg.norm(displacement_vector)
    displacement_alpha = displacement_vector[alpha]
    displacement_beta = displacement_vector[beta]
    displacement_gamma = displacement_vector[gamma]

    return 0.5 * (
        5 * displacement_alpha * displacement_beta * displacement_gamma
        - norm**2
        * (
            displacement_alpha * kronecker_delta(beta, gamma)
            + displacement_beta * kronecker_delta(alpha, gamma)
            + displacement_gamma * kronecker_delta(alpha, beta)
        )
    )


def phi_prime(alpha, beta, gamma, chi, displacement_vector):

    norm = np.linalg.norm(displacement_vector)
    displacement_alpha = displacement_vector[alpha]
    displacement_beta = displacement_vector[beta]
    displacement_gamma = displacement_vector[gamma]
    displacement_chi = displacement_vector[chi]

    0.125 * (
        35
        * displacement_alpha
        * displacement_beta
        * displacement_beta
        * displacement_chi
        - 5
        * norm**2
        * (
            displacement_gamma * displacement_chi * kronecker_delta(alpha, beta)
            + displacement_beta * displacement_gamma * kronecker_delta(alpha, chi)
            + displacement_beta * displacement_chi * kronecker_delta(alpha, gamma)
            + displacement_alpha * displacement_chi * kronecker_delta(beta, gamma)
            + displacement_alpha * displacement_beta * kronecker_delta(gamma, chi)
            + displacement_alpha * displacement_gamma * kronecker_delta(beta, chi)
        )
        + norm**4
        * (
            kronecker_delta(alpha, beta) * kronecker_delta(gamma, chi)
            + kronecker_delta(alpha, gamma) * kronecker_delta(beta, chi)
            + kronecker_delta(alpha, chi) * kronecker_delta(beta, gamma)
        )
    )


def f1(
    alpha: int,
    beta: int,
    gamma: int,
    chi: int,
    dipole: np.ndarray,
    octupole: np.ndarray,
    displacement_vector: np.ndarray,
):
    """_summary_

    :param alpha: first index of Cartesian hexadecapole
    :param beta: second index of Cartesian hexadecapole
    :param gamma: third idex of Cartesian hexadecapole
    :param chi: fourth index of Cartesian hexadecapole
    :param dipole: Cartesian dipole
    :param quadrupole: Cartesian quadrupole
    :param octupole: Cartesian octupole
    """

    dipole_alpha = dipole[alpha]
    oct_prime = omega_prime(beta, gamma, chi, displacement_vector)
    dipole_prime = mu_prime(alpha, displacement_vector)
    oct_beta_gamma_chi = octupole[beta, gamma, chi]

    return dipole_alpha * oct_prime + dipole_prime * oct_beta_gamma_chi


def f2(alpha, beta, gamma, chi, quadrupole, displacement_vector):

    theta_alpha_beta = quadrupole[alpha, beta]
    theta_gamma_chi_prime = theta_prime(gamma, chi, displacement_vector)
    theta_alpha_beta_prime = theta_prime(alpha, beta, displacement_vector)
    theta_gamma_chi = quadrupole[gamma, chi]

    return (
        theta_alpha_beta * theta_gamma_chi_prime
        + theta_alpha_beta_prime * theta_gamma_chi
    )


def eta1_alpha(alpha):

    if alpha == 0:
        return [1, 2, 3]
    elif alpha == 1:
        return [0, 2, 3]
    elif alpha == 2:
        return [0, 1, 3]
    elif alpha == 3:
        return [0, 1, 2]


def eta2_alpha_gamma(alpha, gamma):

    pass


# def G(alpha, beta, gamma, chi, dipole, quadripole, octupole, hexadecupole, displacement_vector):

#     term1 = 24 * f1(alpha, alpha, alpha, alpha, dipole, octupole, displacement_vector)

# eta1 =
