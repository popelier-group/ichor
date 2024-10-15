from collections import Counter
from typing import List, Tuple, Union

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


def hexadecapole_element_conversion(
    hexadecapole_array: np.ndarray, current_ordering: int
):
    """Converts between the (unpacked) two ways of reporting hexadecapole moments, namely

      0:  XXXX, YYYY, ZZZZ, XXXY, XXXZ, YYYX, YYYZ, ZZZX, ZZZY, XXYY, XXZZ,
        YYZZ, XXYZ, YYXZ, ZZXY (this is the ordering given in Gaussian)
      and
      1: XXXX, XXXY, XXXZ, XXYY, XXYZ, XXZZ, XYYY, XYYZ, XYZZ, XZZZ, YYYY,
        YYYZ, YYZZ, YZZZ, ZZZZ

      where the 0 and 1 indicate the current ordering style.

      ..note::
        The other ordering is going to be returned.
        If 0 is given as current ordering, ordering 1 is going to be returned.
        If 1 is given as current ordering, ordering 0 is going to be returned.

    :param hexadecapole_array: 1d unpacked hexadecapole array
    :param current_ordering: either 0 or 1
    :returns: The other ordering of the unpacked hexadecapole array
    """

    if current_ordering == 0:
        return hexadecapole_array[[0, 3, 4, 9, 12, 10, 5, 13, 14, 7, 1, 6, 11, 8, 2]]

    elif current_ordering == 1:
        return hexadecapole_array[[0, 10, 14, 1, 2, 6, 11, 9, 13, 3, 5, 12, 4, 7, 8]]

    raise ValueError(
        f"Current ordering can be either 0 or 1, but it is {current_ordering}"
    )


def hexadecapole_nontraceless_to_traceless(hexadecapole_tensor: np.ndarray):
    """Converts a non-traceless hexadecapole to a traceless hexadecapole tensor.
    GAUSSIAN and ORCA, as well as other computational chemistry software
    usually only give the non-traceless hexadecapole moments. These must
    be converted to traceless ones in order to be compared to AIMAll
    recovered multipole moments.

    :param hexadecapole_tensor: The packed (Cartesian) octupole tensor (of shape 3x3x3x3)
    :returns: The traceless packed (Cartesian) hexadecapole tensor
    """

    # make a temporary tensor which will contain the things we need to subtract off from each term
    tensor_to_subtract = np.zeros((3, 3, 3, 3))

    # Equation 157 from  https://doi.org/10.1016/S1380-7323(02)80033-4
    # Chapter Seven - Post Dirac-Hartree-Fock Methods - Properties by Trond Saue
    # in that equation, pull out the 35 factor so you get (35/8) * (Q_{ijkl}....)
    # that will lead to the equations below

    for i in range(3):
        for j in range(3):
            for k in range(3):
                for l in range(3):
                    tensor_to_subtract[i, j, k, l] += (1 / 7) * (
                        (np.einsum("mm", hexadecapole_tensor[k, l]))
                        * kronecker_delta(i, j)
                        + (np.einsum("mm", hexadecapole_tensor[j, l]))
                        * kronecker_delta(i, k)
                        + (np.einsum("mm", hexadecapole_tensor[j, k]))
                        * kronecker_delta(i, l)
                        + (np.einsum("mm", hexadecapole_tensor[i, l]))
                        * kronecker_delta(j, k)
                        + (np.einsum("mm", hexadecapole_tensor[i, k]))
                        * kronecker_delta(j, l)
                        + (np.einsum("mm", hexadecapole_tensor[i, l]))
                        * kronecker_delta(k, l)
                    ) - (
                        (
                            kronecker_delta(i, j) * kronecker_delta(k, l)
                            + kronecker_delta(i, k) * kronecker_delta(j, l)
                            + kronecker_delta(i, l) * kronecker_delta(j, k)
                        )
                        * np.einsum("mmnn", hexadecapole_tensor * (1 / 35))
                    )

    return hexadecapole_tensor - tensor_to_subtract


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

    return 0.125 * (
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


def f3(
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


def f4(alpha, beta, gamma, chi, quadrupole, displacement_vector):

    theta_alpha_beta = quadrupole[alpha, beta]
    theta_gamma_chi_prime = theta_prime(gamma, chi, displacement_vector)
    theta_alpha_beta_prime = theta_prime(alpha, beta, displacement_vector)
    theta_gamma_chi = quadrupole[gamma, chi]

    return (
        theta_alpha_beta * theta_gamma_chi_prime
        + theta_alpha_beta_prime * theta_gamma_chi
    )


def get_other_alphas(alpha: int) -> Tuple[int, int]:
    """Calculates the 1alpha, and 2alpha terms.
    These must be different than the input alpha.

    :param alpha: 0, 1, or 2 (corresponding to x,y or z)
    :returns: The onealpha, and twoalpha terms
    """

    if alpha == 0:
        return 1, 2
    elif alpha == 1:
        return 0, 2
    elif alpha == 2:
        return 0, 1


def get_alphagamma(alpha: int, gamma: int) -> int:
    """Calculates the alphagamma term, which is defined to be
    alphagamma != alpha != gamma, e.g. if alpha=0, and gamma=1,
    this function will return 2

    :param alpha: 0, 1, or 2 (corresponding to x,y, or z)
    :param gamma: 0, 1, or 2 (corresponding to x,y, or z)
    :return: the remaining term
    """

    for i in range(3):
        if (i != alpha) and (i != gamma):
            return i


def sorting_function(alpha: int, beta: int, gamma: int, chi: int):
    """Sorts the alpha, beta, gamma, chi so that
    the most repeated index is first. Note that
    at least one of the index will be repeating because
    there are four inputs (alpha, beta, gamma, chi)
    but they can only equal 0, 1, or 2 (corresponding to x, y, or z)

    :param alpha: 0, 1, or 2 (corresponding to x,y, or z)
    :param beta: 0, 1, or 2 (corresponding to x,y, or z)
    :param gamma: 0, 1, or 2 (corresponding to x,y, or z)
    :param chi: 0, 1, or 2 (corresponding to x,y, or z)
    """
    li = [alpha, beta, gamma, chi]

    # https://stackoverflow.com/a/23429481
    sorted_li = sorted(li, key=Counter(li).get, reverse=True)

    # there will always be at least one repeating index
    # the 0 and 1 indices will always be repeating
    # this is where the alpha, alpha, beta, gamma) comes from
    return sorted_li[0], sorted_li[2], sorted_li[3]


def G(alpha, beta, gamma, chi, dipole, quadrupole, octupole, displacement_vector):

    # sort by number of repeating indices
    # the largest amount of repetitions are on the left
    # eg. yxxx becomes xxxy, xyzx becomes xxyz, xxxx is xxxx
    # there will always be at least one repeated index
    alpha, beta, gamma = sorting_function(alpha, beta, gamma, chi)

    onealpha, twoalpha = get_other_alphas(alpha)
    alphagamma = get_alphagamma(alpha, gamma)

    if (alpha == beta) and (beta == gamma):

        term1 = 24 * f3(
            alpha, alpha, alpha, alpha, dipole, octupole, displacement_vector
        )
        term2 = 18 * (
            f3(onealpha, onealpha, alpha, alpha, dipole, octupole, displacement_vector)
            + f3(
                twoalpha, twoalpha, alpha, alpha, dipole, octupole, displacement_vector
            )
        )
        term3 = 18 * f4(alpha, alpha, alpha, alpha, quadrupole, displacement_vector)
        term4 = f4(
            onealpha, onealpha, onealpha, onealpha, quadrupole, displacement_vector
        )
        term5 = 2 * f4(
            onealpha, onealpha, twoalpha, twoalpha, quadrupole, displacement_vector
        )
        term6 = f4(
            twoalpha, twoalpha, twoalpha, twoalpha, quadrupole, displacement_vector
        )
        term7 = 16 * (
            f4(alpha, onealpha, alpha, onealpha, quadrupole, displacement_vector)
            + f4(alpha, twoalpha, alpha, twoalpha, quadrupole, displacement_vector)
        )
        term8 = 4 * f4(
            onealpha, twoalpha, onealpha, twoalpha, quadrupole, displacement_vector
        )

        return term1 - term2 + term3 + term4 - term5 + term6 - term7 + term8

    elif (alpha == beta) and (beta != gamma):

        term1 = 10.5 * f3(
            gamma, alpha, alpha, alpha, dipole, octupole, displacement_vector
        )
        term2 = 9 * f3(
            gamma, alpha, gamma, gamma, dipole, octupole, displacement_vector
        )
        term3 = 22.5 * f3(
            alpha, gamma, alpha, alpha, dipole, octupole, displacement_vector
        )
        term4 = 9 * f3(
            alphagamma, gamma, alpha, alphagamma, dipole, octupole, displacement_vector
        )
        term5 = 35 * f4(alpha, alpha, alpha, gamma, quadrupole, displacement_vector)
        term6 = 10 * (
            f4(alpha, gamma, alphagamma, alphagamma, quadrupole, displacement_vector)
            - f4(alpha, alphagamma, gamma, alphagamma, quadrupole, displacement_vector)
        )

        return term1 - term2 + term3 - term4 + term5 + term6

    elif (alpha != beta) and (beta == gamma):

        term1 = 18 * (
            f3(alpha, alpha, gamma, gamma, dipole, octupole, displacement_vector)
            + f3(gamma, gamma, alpha, alpha, dipole, octupole, displacement_vector)
        )
        term2 = 3 * (
            f3(alpha, alpha, alpha, alpha, dipole, octupole, displacement_vector)
            + f3(gamma, gamma, gamma, gamma, dipole, octupole, displacement_vector)
            + f3(
                alphagamma,
                alphagamma,
                alpha,
                alpha,
                dipole,
                octupole,
                displacement_vector,
            )
            + f3(
                alphagamma,
                alphagamma,
                gamma,
                gamma,
                dipole,
                octupole,
                displacement_vector,
            )
        )
        term3 = (35 / 3) * f4(
            alpha, alpha, gamma, gamma, quadrupole, displacement_vector
        )
        term4 = (8 / 3) * (
            f4(alpha, alpha, alpha, alpha, quadrupole, displacement_vector)
            + f4(gamma, gamma, gamma, gamma, quadrupole, displacement_vector)
        )
        term5 = (2 / 3) * f4(
            alphagamma,
            alphagamma,
            alphagamma,
            alphagamma,
            quadrupole,
            displacement_vector,
        )
        term6 = 18 * f4(alpha, gamma, alpha, gamma, quadrupole, displacement_vector)
        term7 = 2 * (
            f4(alpha, alphagamma, alpha, alphagamma, quadrupole, displacement_vector)
            + f4(gamma, alphagamma, gamma, alphagamma, quadrupole, displacement_vector)
        )

        return term1 - term2 + term3 - term4 + term5 + term6 - term7

    else:

        term1 = 18 * f3(
            alpha, alpha, beta, gamma, dipole, octupole, displacement_vector
        )
        term2 = 10.5 * (
            f3(beta, gamma, alpha, alpha, dipole, octupole, displacement_vector)
            + f3(gamma, beta, alpha, alpha, dipole, octupole, displacement_vector)
        )
        term3 = 3 * (
            f3(beta, gamma, beta, beta, dipole, octupole, displacement_vector)
            + f3(gamma, beta, gamma, gamma, dipole, octupole, displacement_vector)
        )
        term4 = 15 * f4(alpha, alpha, beta, gamma, quadrupole, displacement_vector)
        term5 = 20 * f4(alpha, beta, alpha, gamma, quadrupole, displacement_vector)

        return term1 + term2 - term3 + term4 + term5


def hexadecapole_one_term_general_expression(
    alpha: int,
    beta: int,
    gamma: int,
    chi: int,
    displacement_vector: np.ndarray,
    monopole: float,
    dipole: np.ndarray,
    quadrupole: np.ndarray,
    octupole: np.ndarray,
    hexadecapole: np.ndarray,
):
    """
    Calculates a single component of the displaced hexadecapole tensor

    :param alpha: 0 1 2 or 3 for dimension index
    :param beta: 0 1 2 or 3 for dimension index
    :param gamma: 0 1 2 or 3 for dimension index
    :param chi: 0 1 2 or 3 for dimension index
    :param displacement vector: displacement vector containing x,y,z displacement
    :param monopole: Monopole moment, single float
    :param dipole: Dipole moment vector, needs to be a vector of shape 3
    :param quadrupole: Quadrupole moment matrix, needs to be 3x3 matrix
    :param octupole: Octupole moment tensor, needs to be a 3x3x3 tensor
    :param hexadecapole: hexadecapole moment tensor, needs to be a 3x3x3x3 tensor
    :returns: Returns a single element of the Cartesian hexadecapole tensor,
        Phi_{alpha, beta, gamma, chi} that has been displaced by x y z coordinates
    """

    return (
        hexadecapole[alpha, beta, gamma, chi]
        + phi_prime(alpha, beta, gamma, chi, displacement_vector) * monopole
        + (1 / 6)
        * G(alpha, beta, gamma, chi, dipole, quadrupole, octupole, displacement_vector)
    )


def displace_hexadecapole_cartesian(
    displacement_vector: np.array,
    monopole: float,
    dipole: np.ndarray,
    quadrupole: np.ndarray,
    octupole: np.ndarray,
    hexadecapole: np.ndarray,
):
    """Calculates a new octupole moment displaced by a displacement vector

    :param displacement_vector: array containing x, y, z components of shape 3,
    :param monopole: monopole moment (charge), float
    :param dipole: dipole moment, array of shape 3,
    :param quadrupole: quadrupole moment, matrix of shape 3,3
    :param octupole: octupole moment, tensor of shape 3,3,3
    :param hexadecapole: hexadecapole moment, tensor of shape 3,3,3,3
    :return: The displaced hexadecapole moment as array of shape 3,3,3,3
    :rtype: np.ndarray
    """

    assert displacement_vector.shape == (3,)
    # check that arrays are packed multipole moments
    assert isinstance(monopole, float)
    assert dipole.shape == (3,)
    assert quadrupole.shape == (3, 3)
    assert octupole.shape == (3, 3, 3)
    assert hexadecapole.shape == (3, 3, 3, 3)

    res = np.zeros_like(hexadecapole)

    for i in range(3):
        for j in range(3):
            for k in range(3):
                for l in range(3):
                    res[i, j, k, l] = hexadecapole_one_term_general_expression(
                        i,
                        j,
                        k,
                        l,
                        displacement_vector,
                        monopole,
                        dipole,
                        quadrupole,
                        octupole,
                        hexadecapole,
                    )

    return res


def recover_molecular_hexadecapole(
    atoms: Union["ichor.core.Atoms", List["Atoms"]],  # noqa F821
    ints_dir: "ichor.core.files.IntDirectory",  # noqa F821
    convert_to_debye_angstrom_cubed=True,
    convert_to_cartesian=True,
    include_prefactor=True,
):

    from ichor.core.multipoles.dipole import dipole_spherical_to_cartesian
    from ichor.core.multipoles.octupole import octupole_spherical_to_cartesian
    from ichor.core.multipoles.quadrupole import quadrupole_spherical_to_cartesian

    atoms = [a.to_bohr() for a in atoms]

    prefactor = 8 / 35

    molecular_hexadecapole_displaced = np.zeros((3, 3, 3, 3))

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
        q31c = global_multipoles["q31c"]
        q31s = global_multipoles["q31s"]
        q32c = global_multipoles["q32c"]
        q32s = global_multipoles["q32s"]
        q33c = global_multipoles["q33c"]
        q33s = global_multipoles["q33s"]
        q40 = global_multipoles["q40"]
        q41c = global_multipoles["q41c"]
        q41s = global_multipoles["q41s"]
        q42c = global_multipoles["q42c"]
        q42s = global_multipoles["q42s"]
        q43c = global_multipoles["q43c"]
        q43s = global_multipoles["q43s"]
        q44c = global_multipoles["q44c"]
        q44s = global_multipoles["q44s"]

        # get packed representation of all moments we need
        dipole_packed = dipole_spherical_to_cartesian(q10, q11c, q11s)
        quadrupole_packed = quadrupole_spherical_to_cartesian(
            q20, q21c, q21s, q22c, q22s
        )
        octupole_packed = octupole_spherical_to_cartesian(
            q30, q31c, q31s, q32c, q32s, q33c, q33s
        )
        hexadecapole_packed = hexadecapole_spherical_to_cartesian(
            q40, q41c, q41s, q42c, q42s, q43c, q43s, q44c, q44s
        )

        displaced_hexadecapole_cart = displace_hexadecapole_cartesian(
            atom_coords,
            q00,
            dipole_packed,
            quadrupole_packed,
            octupole_packed,
            hexadecapole_packed,
        )

        molecular_hexadecapole_displaced += displaced_hexadecapole_cart

    if include_prefactor:
        molecular_hexadecapole_displaced *= prefactor

    if convert_to_debye_angstrom_cubed:
        molecular_hexadecapole_displaced *= (
            constants.coulombbohrcubed_to_debyeangstromcubed
        )

    if convert_to_cartesian:
        return molecular_hexadecapole_displaced
    else:
        return np.array(
            hexadecapole_cartesian_to_spherical(molecular_hexadecapole_displaced)
        )


def get_gaussian_and_aimall_molecular_hexadecapole(
    gaussian_output: "ichor.core.files.GaussianOutput",  # noqa F821
    ints_directory: "ichor.core.files.IntsDir",  # noqa: F821
    atom_names: list = None,
):
    """Gets the Gaussian hexadecapole moment and converts it to traceless (still in Debye Angstrom^3)
    Also gets the AIMAll recovered molecule hexadecapole moment from atomic ones.

    Returns a tuple of numpy arrays, where the first one is the
    Gaussian traceless 3x3x3x3 hexadecapole moment (in Debye Angstrom^3)
    and the second one is the AIMAll recovered traceless 3x3x3x3
    hexadecapole moment (also converted from au to Debye Angstrom^3)
    and with prefactor taken into account.

    This allows for direct comparison of AIMAll to Gaussian.

    :param gaussian_output: A Gaussian output file containing molecular
        multipole moments and geometry. The same geometry and level of theory
        must also be used in the AIMAll calculation.
    :param ints_directory: A IntsDirectory instance containing the
        AIMAll .int files for the same geometry that was used in Gaussian
    :param atom_names: Optional list of atom names, which represent a subset of
        the atoms. The atomic multipole moments for this subset of atoms will be summed
    :return: A tuple of 3x3x3x3 np.ndarrays, where the first is the Gaussian
        hexadecapole moment and the second is the AIMAll recovered hexadecapole moment.
    """

    # in angstroms, convert to bohr
    atoms = gaussian_output.atoms
    atoms = atoms.to_bohr()

    if atom_names:
        # ensure that the passed in atom names are a subset of the all of the atom names
        if not set(atom_names).issubset(set(atoms.names)):
            raise ValueError(
                f"The passed atom names : {atom_names} must be a subset of all the atom names {atoms.names}."
            )

        atoms = [i for i in atoms if i.name in atom_names]

    # in debye angstrom squared
    raw_gaussian_octupole = np.array(gaussian_output.molecular_hexadecapole)
    # convert to xxx xxy xxz xyy xyz xzz yyy yyz yzz zzz
    # because Gaussian uses a different ordering
    converted_gaussian_hexadecapole = hexadecapole_element_conversion(
        raw_gaussian_octupole, 0
    )
    # pack into 3x3x3x3 array
    packed_converted_gaussian_hexadecapole = pack_cartesian_hexadecapole(
        *converted_gaussian_hexadecapole
    )
    # convert Gaussian to traceless because AIMAll moments are traceless
    traceless_gaussian_octupole = hexadecapole_nontraceless_to_traceless(
        packed_converted_gaussian_hexadecapole
    )
    # note that conversion factors are applied in the function by default
    aimall_recovered_molecular_octupole = recover_molecular_hexadecapole(
        atoms, ints_directory
    )

    return traceless_gaussian_octupole, aimall_recovered_molecular_octupole
