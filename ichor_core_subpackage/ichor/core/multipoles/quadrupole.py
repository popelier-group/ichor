from typing import Tuple

import numpy as np
from ichor.core.common import constants


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


def quadrupole_spherical_to_cartesian(q20, q21c, q21s, q22c, q22s) -> np.ndarray:
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
    return np.array([[q_xx, q_xy, q_xz], [q_xy, q_yy, q_yz], [q_xz, q_yz, q_zz]])


def unpack_cartesian_quadrupole(q):
    return q[0, 0], q[0, 1], q[0, 2], q[1, 1], q[1, 2], q[2, 2]


def quadrupole_rotate_cartesian(q: np.ndarray, C: np.ndarray) -> np.ndarray:
    return np.einsum("ia,jb,ab->ij", C, C, q)


# equations below come from
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


def q20_prime(
    q20: float,
    q10: float,
    q11c: float,
    q11s: float,
    q00: float,
    r_x: float,
    r_y: float,
    r_z: float,
):
    """Calculates math:Q'_{20}:, representing the total ATOMIC contribution for the molecular
    quadrupole math:Q_{20}:

    .. note::
        This is the contribution of one atom, which needs to be summed over to get the molecular value.
        Also, make sure the units for multipole moments / distances are correct.

    :param q20: AIMAll q20 value
    :param q10: AIMAll q10 value
    :param q11c: AIMAll q11c value
    :param q11s: AIMAll q11s value
    :param q00: The charge of the atom (q00). Note that this AIMAll gives q00 without adding the nuclear charge.
        When obtaining q00 through ichor, the nuclear charge is always added to the q00 value.
    :param r_x: Distance of atom from the origin in the x-direction. In Bohr.
    :param r_y: Distance of atom from the origin in the y-direction. In Bohr.
    :param r_z: Distance of atom from the origin in the z-direction. In Bohr.
    """

    return (
        q20
        + 2 * r_z * q10
        - r_x * q11c
        - r_y * q11s
        + 1 / 2 * (3 * r_z**2 - (r_z**2 + r_x**2 + r_y**2)) * q00
    )


def q21c_prime(
    q21c: float, q11c: float, q10: float, q00: float, r_x: float, r_z: float
):
    """Calculates math:Q'_{21c}:, representing the total ATOMIC contribution for the molecular
    quadrupole math:Q_{21c}:

    .. note::
        This is the contribution of one atom, which needs to be summed over to get the molecular value.
        Also, make sure the units for multipole moments / distances are correct.

    :param q21c: AIMAll q21c value
    :param q11c: AIMAll q11c value
    :param q10: AIMAll q10 value
    :param q00: The charge of the atom (q00). Note that this AIMAll gives q00 without adding the nuclear charge.
        When obtaining q00 through ichor, the nuclear charge is always added to the q00 value.
    :param r_x: Distance of atom from the origin in the x-direction. In Bohr.
    :param r_z: Distance of atom from the origin in the z-direction. In Bohr.
    """

    return (
        q21c
        + np.sqrt(3) * r_z * q11c
        + np.sqrt(3) * r_x * q10
        + np.sqrt(3) * r_x * r_z * q00
    )


def q21s_prime(
    q21s: float, q11s: float, q10: float, q00: float, r_y: float, r_z: float
):
    """Calculates math:Q'_{21s}:, representing the total ATOMIC contribution for the molecular
    quadrupole math:Q_{21s}:

    .. note::
        This is the contribution of one atom, which needs to be summed over to get the molecular value.
        Also, make sure the units for multipole moments / distances are correct.

    :param q21s: AIMAll q21s value
    :param q11s: AIMAll q11s value
    :param q10: AIMAll q10 value
    :param q00: The charge of the atom (q00). Note that this AIMAll gives q00 without adding the nuclear charge.
        When obtaining q00 through ichor, the nuclear charge is always added to the q00 value.
    :param r_y: Distance of atom from the origin in the y-direction. In Bohr.
    :param r_z: Distance of atom from the origin in the z-direction. In Bohr.
    """

    return (
        q21s
        + np.sqrt(3) * r_z * q11s
        + np.sqrt(3) * r_y * q10
        + np.sqrt(3) * r_y * r_z * q00
    )


def q22c_prime(
    q22c: float, q11c: float, q11s: float, q00: float, r_x: float, r_y: float
):
    """Calculates math:Q'_{22c}:, representing the total ATOMIC contribution for the molecular
    quadrupole math:Q_{22c}:

    .. note::
        This is the contribution of one atom, which needs to be summed over to get the molecular value.
        Also, make sure the units for multipole moments / distances are correct.

    :param q22c: AIMAll q22c value
    :param q11c: AIMAll q11c value
    :param q11s: AIMAll q11s value
    :param q00: The charge of the atom (q00). Note that this AIMAll gives q00 without adding the nuclear charge.
        When obtaining q00 through ichor, the nuclear charge is always added to the q00 value.
    :param r_x: Distance of atom from the origin in the x-direction. In Bohr.
    :param r_y: Distance of atom from the origin in the y-direction. In Bohr.
    """

    return (
        q22c
        + np.sqrt(3) * r_x * q11c
        - np.sqrt(3) * r_y * q11s
        + (np.sqrt(3) / 2) * (r_x**2 * r_y**2) * q00
    )


def q22s_prime(
    q22s: float, q11c: float, q11s: float, q00: float, r_x: float, r_y: float
):
    """Calculates math:Q'_{22s}:, representing the total ATOMIC contribution for the molecular
    quadrupole math:Q_{22s}:

    .. note::
        This is the contribution of one atom, which needs to be summed over to get the molecular value.
        Also, make sure the units for multipole moments / distances are correct.

    :param q22s: AIMAll q22s value
    :param q11c: AIMAll q11c value
    :param q11s: AIMAll q11s value
    :param q00: The charge of the atom (q00). Note that this AIMAll gives q00 without adding the nuclear charge.
        When obtaining q00 through ichor, the nuclear charge is always added to the q00 value.
    :param r_x: Distance of atom from the origin in the x-direction. In Bohr.
    :param r_y: Distance of atom from the origin in the y-direction. In Bohr.
    """

    return (
        q22s
        + np.sqrt(3) * r_y * q11c
        + np.sqrt(3) * r_x * q11s
        + np.sqrt(3) * r_x * r_y * q00
    )


def atomic_contribution_to_molecular_quadrupole(
    q00, q10, q11c, q11s, q20, q21c, q21s, q22c, q22s, atomic_coordinates
):
    """Calculates the atomic contribution to the molecular quadrupole moment.
    Note that the moments are in spherical coordinates.
    Atomic coordinates are assumed to be Bohr.

    .. note::
        This is contribution of ONE atom.

    :param q00: The charge of the atom (q00). Note that this AIMAll gives q00 without adding the nuclear charge.
        When obtaining q00 through ichor, the nuclear charge is always added to the q00 value.
    :param q10: AIMAll q10 value
    :param q11c: AIMAll q11c value
    :param q11s: AIMAll q11s value
    :param q20: AIMAll q20 value
    :param q21c: AIMAll q21c value
    :param q21s: AIMAll q21s value
    :param q22c: AIMAll q22c value
    :param q22s: AIMAll q22s value
    :param atomic_coordinates: 1D numpy array containing the x,y,z values (in bohr)
    """

    q20_pr = q20_prime(q20, q10, q11c, q11s, q00, *atomic_coordinates)
    q21c_pr = q21c_prime(
        q21c, q11c, q10, q00, atomic_coordinates[0], atomic_coordinates[2]
    )
    q21s_pr = q21s_prime(
        q21s, q11s, q10, q00, atomic_coordinates[1], atomic_coordinates[2]
    )
    q22c_pr = q22c_prime(
        q22c, q11c, q11s, q00, atomic_coordinates[0], atomic_coordinates[1]
    )
    q22s_pr = q22s_prime(
        q22s, q11c, q11s, q00, atomic_coordinates[0], atomic_coordinates[1]
    )

    return np.array([q20_pr, q21c_pr, q21s_pr, q22c_pr, q22s_pr])
