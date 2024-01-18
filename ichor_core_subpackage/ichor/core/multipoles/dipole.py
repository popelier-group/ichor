from typing import Tuple

import numpy as np


def rotate_dipole(
    q10: float, q11c: float, q11s: float, C: np.ndarray
) -> Tuple[float, float, float]:
    """Rotates dipole moment from global spherical to local spherical.

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


# equations come from
# https://doi.org/10.1021/jp067922u
# The effects of hydrogen-bonding environment on the polarization and electronic properties of water molecules
# https://doi.org/10.1080/15533170701854189
# The Asymptotic Behavior of the Dipole and Quadrupole Moment of a Single Water Molecule from Gas Phase to
# Large Clusters: A QCT Analysis

# note that the units for distances are in Bohr
# Gaussian calculates multipole moments in Debye, while atomic units are using in AIMAll (Coulomb Bohr)
# TODO: Gaussian defines the x,y,z axes a different way, therefore the values are switched around for dipole moment.
# TODO: Figure out how axes are swapped and what changes that has on quadrupole, octupole, hexadecapole values

# You should be able to recover the Gaussain molecular values by
# doing the necessary conversions of AIMAll values and summing across all atoms
# Note that the axes that Gaussian uses are different though.
# Importantly, there is NO NEED to rotate multipole moments in ALF frame if directly comparing AIMAll and Gaussian
# however, if making predictions with FFLUX, you WILL need to
# convert the local multipole moments to the global frame before summing up the components
# across atoms/molecules. Otherwise you will get the wrong answer.

# note that AIMAll multipole moments are in Spherical coordinates but Gaussian ones are in Cartesian
# for dipole moment, the number of values for spherical/Cartesian is the same (3)
# for higher multipole moments, there are less spherical ones than Cartesian


def q10_prime(q10: float, r_z: float, q00: float):
    """Calculates math:Q'_{10}, representing the total ATOMIC contribution for the molecular
    dipole moment.

    .. note::
        This is the contribution of one atom, which needs to be summed over to get the molecular value.
        Also, make sure the units for multipole moments / distances are correct.

    :param q_10: AIMAll Q_10 value
    :param r_z: Distance of atom from the origin in the z-direction. In Bohr.
    :param q_omega: The charge of the atom (q00). Note that this AIMAll gives q00 without adding the nuclear charge.
        When obtaining q00 through ichor, the nuclear charge is always added to the q00 value.
    """

    return q10 + r_z * q00


def q11c_prime(q11c: float, r_x: float, q00: float):
    """Calculates math:Q'_{11c}, representing the total ATOMIC contribution for the molecular
    dipole moment.

    .. note::
        This is the contribution of one atom, which needs to be summed over to get the molecular value.
        Also, make sure the units for multipole moments / distances are correct.

    :param q_10: AIMAll Q_11c value
    :param r_x: Distance of atom from the origin in the x-direction. In Bohr.
    :param q_omega: The charge of the atom (q00). Note that this AIMAll gives q00 without adding the nuclear charge.
        When obtaining q00 through ichor, the nuclear charge is always added to the q00 value.
    """

    return q11c + r_x * q00


def q11s_prime(q11s: float, r_y: float, q00: float):
    """Calculates math:Q'_{11s}, representing the total ATOMIC contribution for the molecular
    dipole moment.

    .. note::
        This is the contribution of one atom, which needs to be summed over to get the molecular value.
        Also, make sure the units for multipole moments / distances are correct.

    :param q_10: AIMAll Q_11c value
    :param r_y: Distance of atom from the origin in the y-direction. In Bohr.
    :param q_omega: The charge of the atom (q00). Note that this AIMAll gives q00 without adding the nuclear charge.
        When obtaining q00 through ichor, the nuclear charge is always added to the q00 value.
    """

    return q11s + r_y * q00


def atomic_contribution_to_molecular_dipole(
    q00, q10: float, q11c: float, q11s: float, atomic_coordinates: np.ndarray
):
    """Calculates the atomic contribution to the molecular dipole moment.

    .. note::
        This is contribution of ONE atom.

    :param q10: AIMAll q10 value
    :param q11c: AIMAll q11c value
    :param q11s: AIMAll q11s value
    :param atomic_coordinates: 1D numpy array containing the x,y,z values (in bohr)
    """

    q10_pr = q10_prime(q10, atomic_coordinates[2], q00)
    q11c_pr = q11c_prime(q11c, atomic_coordinates[0], q00)
    q11s_pr = q11s_prime(q11s, atomic_coordinates[1], q00)

    return np.array([q10_pr, q11c_pr, q11s_pr])
