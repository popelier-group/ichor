from typing import Tuple

import numpy as np
from ichor.core.common import constants
from ichor.core.common.constants import coulombbhrsquared_to_debye_angstrom


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
# Gaussian calculates multipole moments in Debye, while atomic units are using in AIMAll
# Units for quadrupole are Coulomb Bohr**2
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
        + (2 * r_z * q10)
        - (r_x * q11c)
        - (r_y * q11s)
        + (0.5 * ((3 * r_z**2) - (r_x**2 + r_y**2 + r_z**2)) * q00)
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
        + (constants.rt3 * r_z * q11c)
        + (constants.rt3 * r_x * q10)
        + (constants.rt3 * r_x * r_z * q00)
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
        + (constants.rt3 * r_z * q11s)
        + (constants.rt3 * r_y * q10)
        + (constants.rt3 * r_y * r_z * q00)
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
        + (constants.rt3 * r_x * q11c)
        - (constants.rt3 * r_y * q11s)
        + ((constants.rt3 / 2.0) * (r_x**2 - r_y**2) * q00)
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
        + (constants.rt3 * r_y * q11c)
        + (constants.rt3 * r_x * q11s)
        + (constants.rt3 * r_x * r_y * q00)
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


def recover_molecular_quadrupole(
    atoms: "Atoms",  # noqa
    ints_dir: "IntDirectory",  # noqa
    atoms_in_angstroms=True,
    convert_to_debye_angstrom=True,
    convert_to_cartesian=True,
    unpack=True,
    include_prefactor=True,
):
    """
    Reads in a geometry (atoms) and _atomicfiles directory containing AIMAll output files
    and calculates the molecular quadrupole moment of the system (in spherical coordinates)
    from the AIMAll atomic multipole moments.

    .. note::
        Assumes atomic multipole moment units are atomic units (Coulomb Bohr**2) because this is what AIMAll gives.

    :param atoms: an Atoms instance containing the system geometry
    :param ints_dir: an IntDirectory file instance, which wraps around an AIMAll output directory
    :param atoms_in_angstroms: Whether the Atom instance coordinates are in Bohr or Angstroms
        , defaults to True (meaning coordinates are in Angstroms)
    :param convert_to_debye: Whether or not to convert the final result to Debye, default to True.
        This converts from atomic units to Debye.
    :param convert_to_cartesian: Whether or not to convert the recovered molecular quadrupole from spherical
        to Cartesian, defaults to True. Note that Gaussian calculates molecular multipole moments
        in Cartesian coordinates, so set to True in case you are comparing against Gaussian.
    :param unpacked: Whether to unpack the Cartesian quadrupole so it does not have redundancies.
        Note the returned order is xx, xy, xz, yy, yz, zz
    :param prefactor: Include the (3/2) prefactor to directly compare against GAUSSIAN
    :returns: A numpy array containing the molecular quadrupole moment.

    .. note:
        There is a factor of (2/3) that must be included which is excluded from
        GAUSSIAN/ORCA etc. See Anthony Stone Theory of Intermolecular Forces p22-23.
        AIMAll obtains the true quadrupole moment (and the true molecular one can
        be recovered), while GAUSSIAN and ORCA do not include that.
    """

    # make sure we are in Bohr
    if atoms_in_angstroms:
        atoms = atoms.to_bohr()

    # spherical representation
    molecular_quadrupole = np.zeros(5)

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

        atomic_contibution = atomic_contribution_to_molecular_quadrupole(
            q00, q10, q11c, q11s, q20, q21c, q21s, q22c, q22s, atom_coords
        )
        molecular_quadrupole += atomic_contibution

    if convert_to_debye_angstrom:
        molecular_quadrupole *= coulombbhrsquared_to_debye_angstrom

    if convert_to_cartesian:
        molecular_quadrupole = quadrupole_spherical_to_cartesian(*molecular_quadrupole)

        if unpack:
            molecular_quadrupole = np.array(
                unpack_cartesian_quadrupole(molecular_quadrupole)
            )

    if include_prefactor:
        molecular_quadrupole = (2 / 3) * molecular_quadrupole

    return molecular_quadrupole


def molecular_quadrupole_origin_change(
    quadrupole_moment: np.ndarray,
    dipole_moment: np.ndarray,
    old_origin: np.ndarray,
    new_origin: np.ndarray,
    molecular_charge: int,
):
    """Makes an origin change of the quadrupole moment and returns the quadrupole moment from a different origin.
        Note that the returned quadrupole moment is TRACELESS.

    :param quadrupole_moment: A 1d array containing the quadrupole moment in Cartesian coordinates
        from the perspective of the old origin
        HAS TO be ordered as: xx, yy, zz, xy, xz, yz and in atomic units
        also HAS TO BE TRACELESS
        Note that the division by a (2/3) prefactor is included in the implementation
        because the true quadrupole moment is used for the equations.
    :param dipole_moment: A 1d array containing the dipole moment in Cartesian coordinates
        from the perspective of the old origin
        HAS TO be ordered as x, y, z and in atomic units
    :param old_origin: A numpy array containing the old origin x,y,z coordinates in Bohr
    :param new_origin: A numpy array containing the new origin x,y,z coordinates in Bohr
    :param molecular_charge: The charge of the system
    :returns: A numpy array containing the xx, yy, zz, xy, xz, yz TRACELESS components as seen from the new origin

    .. note::

        See p. 21 of Anthony Stone Theory of Intermolecular forces for a discussion on the traceless / nontraceless
        as well as a discussion on the prefactors in the multipole moments.

        Also see https://doi.org/10.1021/jp067922u  The Effects of Hydrogen-Bonding Environment
        on the Polarization and Electronic Properties of Water Molecules
        for the equations. The equations are the for atomic quadrupole moments, however they
        are exactly the same for molecular

    .. note::
        The equations to do the conversion have already been implemented in Spherical coordinates
        to do the AIMAll recovery from atomic to molecular. Therefore, to reuse the code we
        must convert the Cartesian moments to spherical ones.

    .. note::
        To convert to a traceless quadrupole moment, you just subtract take the average of the xx,yy,zz components
        and subtract that from the diagonal (containing the xx,yy,zz components)
    """

    from ichor.core.multipoles.dipole import dipole_cartesian_to_spherical

    # get the true quadrupole moment as would be calculated by AIMAll
    # GAUSSIAN and ORCA do not include this prefactor
    # see p21-p22 in See p. 21 of Anthony Stone Theory of Intermolecular forces
    quadrupole_moment = quadrupole_moment / (2 / 3)

    # we need the dipole in the quadrupole calculations as well
    q10, q11c, q11s = dipole_cartesian_to_spherical(dipole_moment)

    # the packing function uses xx, xy, xz, yy, yz, zz ordering
    # gives a 3x3 matrix containing the packed representation
    packed_traceless_quadrupole = pack_cartesian_quadrupole(
        quadrupole_moment[0],
        quadrupole_moment[3],
        quadrupole_moment[4],
        quadrupole_moment[1],
        quadrupole_moment[5],
        quadrupole_moment[2],
    )

    # convert to spherical because equations we are using are for spherical
    q20, q21c, q21s, q22c, q22s = quadrupole_cartesian_to_spherical(
        packed_traceless_quadrupole
    )

    # this is the quadrupole moment in the new origin
    # but it is in spherical
    quadripole_prime = atomic_contribution_to_molecular_quadrupole(
        molecular_charge,
        q10,
        q11c,
        q11s,
        q20,
        q21c,
        q21s,
        q22c,
        q22s,
        old_origin - new_origin,
    )
    # convert back to cartesian
    quadripole_prime_cartesian = quadrupole_spherical_to_cartesian(*quadripole_prime)

    # take into account factor again so that we can directly compare against GAUSSIAN or ORCA
    # note that this will be in atomic unit still so an additional conversion might be needed
    quadripole_prime_cartesian *= 2 / 3

    # ordered as xx, xy, xz, yy, yz, zz
    unpacked_shifted_origin_quadrupole = np.array(
        unpack_cartesian_quadrupole(quadripole_prime_cartesian)
    )
    # ordered as xx, yy, zz, xy, xz, yz
    unpacked_shifted_origin_quadrupole = unpacked_shifted_origin_quadrupole[
        [0, 3, 5, 1, 2, 4]
    ]

    return unpacked_shifted_origin_quadrupole
