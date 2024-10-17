from typing import List, Tuple, Union

import numpy as np
from ichor.core.common import constants
from ichor.core.common.arith import kronecker_delta
from ichor.core.multipoles.primed_functions import mu_prime, omega_prime, theta_prime

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
    """
    Converts the octupole from spherical to Cartesian tensor form
    Returns a 3x3x3 tensor

    :param q30: q30 spherical tensor component
    :param q31c: q31c spherical tensor component
    :param q31s: q31s spherical tensor component
    :param q32c: q32c spherical tensor component
    :param q32s: q32s spherical tensor component
    :param q33c: q33c spherical tensor component
    :param q33s: q33s spherical tensor component
    :returns: 3x3x3 np.ndarray containing the Cartesian octupole
    """

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
    """Converts the Carteisan tensor octupole into its spherical components.

    :param o: Cartesian octupole of shape 3x3x3
    """

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
    """Packs the Cartesian octupole to form a 3x3x3 tensor"""

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


def unpack_cartesian_octupole(
    o: np.ndarray,
) -> Tuple[float, float, float, float, float, float, float, float, float, float]:
    """Unpacks the Cartesian octupole moment into its unique elements

    :returns: A tuple of the unique Cartesian elements of the octupole moment.
    """
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

      where the 0 and 1 indicate the current ordering style.

      ..note::
        The other ordering is going to be returned.
        If 0 is given as current ordering, ordering 1 is going to be returned.
        If 1 is given as current ordering, ordering 0 is going to be returned.

    :param octupole_array: 1d unpacked octupole array
    :param current_ordering: either 0 or 1
    """

    if current_ordering == 0:
        return octupole_array[[0, 4, 5, 3, 9, 6, 1, 8, 7, 2]]

    elif current_ordering == 1:
        return octupole_array[[0, 6, 9, 3, 1, 2, 5, 8, 7, 4]]

    raise ValueError(
        f"Current ordering can be either 0 or 1, but it is {current_ordering}"
    )


def octupole_rotate_cartesian(o: np.ndarray, C: np.ndarray) -> np.ndarray:
    """Rotates the octupole moment given a rotation matrix C

    :param o: The Cartesian octupole moment (3x3x3 array)
    :param C: The 3x3 rotation matrix
    :returns: The rotated Cartesian octupole moment (3x3x3 array)
    """

    return np.einsum("ia,jb,kc,abc->ijk", C, C, C, o)


def octupole_nontraceless_to_traceless(octupole_tensor: np.ndarray):
    """Converts a non-traceless octupole to a traceless octupole.
    GAUSSIAN and ORCA, as well as other computational chemistry software
    usually only give the non-traceless octupole moments. These must
    be converted to traceless ones in order to be compared to AIMAll
    recovered multipole moments.

    :param octupole_tensor: The packed (Cartesian) octupole tensor
    :returns: The traceless packed (Cartesian) octupole tensor
    """

    # make a temporary tensor which will contain the things we need to subtract off from each term
    tensor_to_subtract = np.zeros((3, 3, 3))

    # Equation 156 from  https://doi.org/10.1016/S1380-7323(02)80033-4
    # Chapter Seven - Post Dirac-Hartree-Fock Methods - Properties by Trond Saue

    for i in range(3):
        for j in range(3):
            for k in range(3):
                tensor_to_subtract[i, j, k] += (
                    1
                    / 5
                    * (
                        (np.einsum("ll", octupole_tensor[i])) * kronecker_delta(j, k)
                        + (np.einsum("ll", octupole_tensor[j])) * kronecker_delta(i, k)
                        + (np.einsum("ll", octupole_tensor[k])) * kronecker_delta(i, j)
                    )
                )

    return octupole_tensor - tensor_to_subtract


def f2(alpha, beta, gamma, dipole, quadrupole, displacement_vector):

    return (
        quadrupole[alpha, beta] * mu_prime(gamma, displacement_vector)
        + theta_prime(alpha, beta, displacement_vector) * dipole[gamma]
    )


def h(alpha, beta, gamma, dipole, quadrupole, displacement_vector):

    last_term = 0.0
    for i in range(3):
        last_term += f2(i, gamma, i, dipole, quadrupole, displacement_vector)

    return (
        5 * f2(alpha, beta, gamma, dipole, quadrupole, displacement_vector)
        - 2 * kronecker_delta(alpha, beta) * last_term
    )


def octupole_one_term_general_expression(
    alpha: int,
    beta: int,
    gamma: int,
    displacement_vector: np.ndarray,
    monopole: float,
    dipole: np.ndarray,
    quadrupole: np.ndarray,
    octupole: np.ndarray,
):
    """
    Calculates a single component of the displaced octupole tensor

    :param alpha: 0 1 or 2 for x,y, or z direction
    :param beta: 0 1 or 2 for x,y, or z direction
    :param gamma: 0 1 or 2 for x,y, or z direction
    :param displacement vector: displacement vector containing x,y,z displacement
    :param monopole: Monopole moment, single float
    :param dipole: Dipole moment vector, needs to be a vector of shape 3
    :param quadrupole: Quadrupole moment matrix, needs to be 3x3 matrix
    :param octupole: Octupole moment tensor, needs to be a 3x3x3 tensor
    :returns: Returns a single element of the Cartesian octupole tensor,
        Omega_{alpha, beta, gamma} that has been displaced by x y z coordinates
    """

    return (
        octupole[alpha, beta, gamma]
        + omega_prime(alpha, beta, gamma, displacement_vector) * monopole
        + (1 / 3)
        * (
            h(alpha, beta, gamma, dipole, quadrupole, displacement_vector)
            + h(alpha, gamma, beta, dipole, quadrupole, displacement_vector)
            + h(beta, gamma, alpha, dipole, quadrupole, displacement_vector)
        )
    )


def displace_octupole_cartesian(
    displacement_vector: np.array,
    monopole: float,
    dipole: np.ndarray,
    quadrupole: np.ndarray,
    octupole: np.ndarray,
):
    """Calculates a new octupole moment displaced by a displacement vector

    :param displacement_vector: array containing x, y, z components of shape 3,
    :param monopole: monopole moment (charge), float
    :param dipole: dipole moment, array of shape 3,
    :param quadrupole: quadrupole moment, matrix of shape 3,3
    :param octupole: octupole moment, tensor of shape 3,3,3
    :return: The displaced octupole moment as array of shape 3,3,3
    :rtype: np.ndarray
    """

    assert displacement_vector.shape == (3,)
    # check that arrays are packed multipole moments
    assert isinstance(monopole, float)
    assert dipole.shape == (3,)
    assert quadrupole.shape == (3, 3)
    assert octupole.shape == (3, 3, 3)

    res = np.zeros_like(octupole)

    for i in range(3):
        for j in range(3):
            for k in range(3):
                res[i, j, k] = octupole_one_term_general_expression(
                    i, j, k, displacement_vector, monopole, dipole, quadrupole, octupole
                )

    return res


def recover_molecular_octupole(
    atoms: Union["ichor.core.Atoms", List["Atoms"]],  # noqa F821
    ints_dir: "ichor.core.files.IntDirectory",  # noqa F821
    convert_to_debye_angstrom_squared=True,
    convert_to_cartesian=True,
    include_prefactor=True,
):
    """Recovers the octupole moment fora collection of atoms.

    .. note::
        The atoms might be a subset of the whole molecule, so the
        calculated octupole moment will be for that fragment only

    :param atoms: The atoms over which to sum the atomic multipole moments
    :param convert_to_cartesian: Whether to return the Cartesian octupole moment or spherical, defaults to True
    :param include_prefactor: Whether to include the (2/5) prefactor, defaults to True
    :return: The recovered octupole moment with origin (0,0,0)
    """

    from ichor.core.multipoles.dipole import dipole_spherical_to_cartesian
    from ichor.core.multipoles.quadrupole import quadrupole_spherical_to_cartesian

    atoms = [a.to_bohr() for a in atoms]

    # from anthony stone theory of intermolecular forces p21-22
    # note that aimall * (2/5) = Gaussian (if both are in atomic units)
    # Gaussian is not in atomic units by default
    prefactor = 2 / 5

    molecular_octupole_displaced = np.zeros((3, 3, 3))

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

        # get packed representation of all moments we need
        dipole_packed = dipole_spherical_to_cartesian(q10, q11c, q11s)
        quadrupole_packed = quadrupole_spherical_to_cartesian(
            q20, q21c, q21s, q22c, q22s
        )
        octupole_packed = octupole_spherical_to_cartesian(
            q30, q31c, q31s, q32c, q32s, q33c, q33s
        )

        displaced_octupole_cart = displace_octupole_cartesian(
            atom_coords, q00, dipole_packed, quadrupole_packed, octupole_packed
        )

        molecular_octupole_displaced += displaced_octupole_cart

    if include_prefactor:
        molecular_octupole_displaced *= prefactor

    if convert_to_debye_angstrom_squared:
        molecular_octupole_displaced *= (
            constants.coulombbohrcubed_to_debyeangstromsquared
        )

    if convert_to_cartesian:
        return molecular_octupole_displaced
    else:
        return np.array(octupole_cartesian_to_spherical(molecular_octupole_displaced))


def get_gaussian_and_aimall_molecular_octupole(
    gaussian_output: "ichor.core.files.GaussianOutput",  # noqa F821
    ints_directory: "ichor.core.files.IntsDir",  # noqa: F821
    atom_names: list = None,
):
    """Gets the Gaussian octupole moment and converts it to traceless (still in Debye Angstrom^2)
    Also gets the AIMAll recovered molecule octupole moment from atomic ones.

    Returns a tuple of numpy arrays, where the first one is the
    Gaussian traceless 3x3x3 octupole moment (in Debye Angstrom^2)
    and the second one is the AIMAll recovered traceless 3x3x3
    octupole moment (also converted from au to Debye Angstrom^2)
    and with prefactor taken into account.

    This allows for direct comparison of AIMAll to Gaussian.

    :param gaussian_output: A Gaussian output file containing molecular
        multipole moments and geometry. The same geometry and level of theory
        must also be used in the AIMAll calculation.
    :param ints_directory: A IntsDirectory instance containing the
        AIMAll .int files for the same geometry that was used in Gaussian
    :param atom_names: Optional list of atom names, which represent a subset of
        the atoms. The atomic multipole moments for this subset of atoms will be summed
    :return: A tuple of 3x3x3 np.ndarrays, where the first is the Gaussian
        octupole moment and the second is the AIMAll recovered octupole moment.
    """

    # in angstroms, convert to bohr
    atoms = gaussian_output.atoms

    if atom_names:
        # ensure that the passed in atom names are a subset of the all of the atom names
        if not set(atom_names).issubset(set(atoms.names)):
            raise ValueError(
                f"The passed atom names : {atom_names} must be a subset of all the atom names {atoms.names}."
            )

        atoms = [i for i in atoms if i.name in atom_names]

    # in debye angstrom squared
    raw_gaussian_octupole = np.array(gaussian_output.molecular_octupole)
    # convert to xxx xxy xxz xyy xyz xzz yyy yyz yzz zzz
    # because Gaussian uses a different ordering
    converted_gaussian_octupole = octupole_element_conversion(raw_gaussian_octupole, 0)
    # pack into 3x3x3 array
    packed_converted_gaussian_octupole = pack_cartesian_octupole(
        *converted_gaussian_octupole
    )
    # convert Gaussian to traceless because AIMAll moments are traceless
    traceless_gaussian_octupole = octupole_nontraceless_to_traceless(
        packed_converted_gaussian_octupole
    )
    # note that conversion factors are applied in the function by default
    aimall_recovered_molecular_octupole = recover_molecular_octupole(
        atoms, ints_directory
    )

    return traceless_gaussian_octupole, aimall_recovered_molecular_octupole
