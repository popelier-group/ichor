from typing import List, Tuple, Union

import numpy as np

from ichor.core.common.constants import coulombbohr_to_debye


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


def dipole_one_term_general_expression(
    alpha: int, displacement_vector: np.ndarray, monopole: float, dipole: np.ndarray
) -> float:
    """Origin chage of the x,y, or z component of the dipole moment by a displacement vector

    :param alpha: 0, 1, or 2 for x, y, or z
    :param displacement_vector: np.ndarray containing x,y,z components of displacement vector
    :param monopole: monopole moment, float (charge of atom or system).
        Note that for AIMAll, the q00 in the AIMAll .int file does not have the nuclear charge added
        ichor automatically does that when parsing .int files.
    :param dipole: The atomic or molecular dipole moment
        np.ndarray containing x,y,z components of displacement vector (Cartesian)
    :returns: The x,y or z component of the dipole moment as seen from a new origin.
    """

    mu_alpha_disp = dipole[alpha] + displacement_vector[alpha] * monopole

    return mu_alpha_disp


def displace_dipole_cartesian(displacement_vector: np.ndarray, monopole: float, dipole):
    """Computes the full displaced dipole moment

    :param displacement_vector: Displacement vector
    :param monopole: monopole moment, float (charge of atom or system).
        Note that for AIMAll, the atomic q00 (monopole) in the AIMAll .int file
        does not have the nuclear charge added
        ichor automatically does that when parsing .int files.
    :param dipole: The atomic or molecular dipole moment
        np.ndarray containing x,y,z components of displacement vector (Cartesian
    :return: np.ndarray of shape 3 containing x,y, and z components of displaced dipole moment
    """

    assert displacement_vector.shape == (3,)
    # check that arrays are packed multipole moments
    assert isinstance(monopole, float)
    assert dipole.shape == (3,)

    res = np.zeros(3)

    for i in range(3):
        res[i] = dipole_one_term_general_expression(
            i, displacement_vector, monopole, dipole
        )

    return res


def recover_molecular_dipole(
    atoms: Union["ichor.core.Atoms", List["Atoms"]],  # noqa F821
    ints_dir: "ichor.core.files.IntDirectory",  # noqa F821
    convert_to_debye=True,
    convert_to_spherical=False,
):
    """
    Calculates the recovered MOLECULAR dipole moment from ATOMIC dipole moments from AIMAll,
    given a geometry (atoms) and an ints_directory, containing the AIMAll calculations for
    the given geometry.

    :param atoms: an Atoms instance containing the system geometry
    :param ints_dir: an IntDirectory file instance, which wraps around an AIMAll output directory
    :param convert_to_debye: Whether or not to convert the final result to Debye, default to True.
        This converts from atomic units to Debye. See Appendix D of Anthony Stone "Theory of
        Intermolecular Forces"
    :param convert_to_cartesian: Whether or not to convert the recovered molecular dipole from spherical
        to Cartesian, defaults to True. Note that Gaussian calculates molecular multipole moments
        in Cartesian coordinates, so set to True in case you are comparing against Gaussian.
    :returns: A numpy array containing the recovered molecular dipole moment.
    """

    atoms = [a.to_bohr() for a in atoms]

    molecular_dipole = np.zeros(3)

    for atom in atoms:

        # get necessary data for calculations
        atom_coords = atom.coordinates
        global_multipoles = ints_dir[atom.name].global_multipole_moments

        # get the values for a particular atom
        q00 = global_multipoles["q00"]
        q10 = global_multipoles["q10"]
        q11c = global_multipoles["q11c"]
        q11s = global_multipoles["q11s"]

        # get packed representation of all moments we need
        dipole_packed_cartesian = dipole_spherical_to_cartesian(q10, q11c, q11s)
        displaced_atomic_dipole = displace_dipole_cartesian(
            atom_coords, q00, dipole_packed_cartesian
        )

        molecular_dipole += displaced_atomic_dipole

    if convert_to_debye:
        molecular_dipole *= coulombbohr_to_debye

    if convert_to_spherical:
        molecular_dipole = dipole_cartesian_to_spherical(*molecular_dipole)

    return molecular_dipole


def get_gaussian_and_aimall_molecular_dipole(
    gaussian_output: "ichor.core.files.GaussianOutput",  # noqa F821
    ints_directory: "ichor.core.files.IntsDir",  # noqa: F821
    atom_names: list = None,
):
    """Gets the Gaussian dipole moment (still in Debye)
    Also gets the AIMAll recovered molecule dipole moment from atomic ones.

    Returns a tuple of numpy arrays, where the first one is the
    Gaussian traceless dipole moment (in Debye)
    and the second one is the AIMAll recovered traceless
    dipole moment (also converted from au to Debye)

    This allows for direct comparison of AIMAll to Gaussian.

    :param gaussian_output: A Gaussian output file containing molecular
        multipole moments and geometry. The same geometry and level of theory
        must also be used in the AIMAll calculation.
    :param ints_directory: A IntsDirectory instance containing the
        AIMAll .int files for the same geometry that was used in Gaussian
    :param atom_names: Optional list of atom names, which represent a subset of
        the atoms. The atomic multipole moments for this subset of atoms will be summed
    :return: A tuple of np.ndarrays of shape (3,) , where the first is the Gaussian
        dipole moment and the second is the AIMAll recovered dipole moment.
    """

    # make sure we are in bohr
    atoms = gaussian_output.atoms
    atoms = atoms.to_bohr()

    if atom_names:
        # ensure that the passed in atom names are a subset of the all of the atom names
        if not set(atom_names).issubset(set(atoms.names)):
            raise ValueError(
                f"The passed atom names : {atom_names} must be a subset of all the atom names {atoms.names}."
            )

        atoms = [i for i in atoms if i.name in atom_names]

    # in debye
    raw_gaussian_dipole = np.array(gaussian_output.molecular_dipole)
    # note that conversion factors are applied in the function by default
    aimall_recovered_molecular_dipole = recover_molecular_dipole(atoms, ints_directory)

    return raw_gaussian_dipole, aimall_recovered_molecular_dipole


# def dipole_origin_change(
#     dipole: np.ndarray,
#     old_origin: np.ndarray,
#     new_origin: np.ndarray,
#     molecular_charge: int,
# ) -> np.ndarray:
#     """Changes the origin of the dipole moment and returns the dipole moment in the new origin

#     :param dipole: a 1-dimensional np.ndarray containing the x,y,z components
#         note the dipole moment has to be in Cartesian coordinates AND in atomic units.
#     :param old_origin: The old origin with respect to which the given dipole is calculated.
#         1d array containing Cartesian x,y,z coordinates in Bohr.
#     :type old_origin: The new origin with respect to which the new dipole should be given.
#         1d array containing Cartesian x,y,z coordinates in Bohr.
#     :param molecular_charge: The charge of the system (positive or negative)
#     :return: The dipole moment as seen from the new origin, in atomic units

#     See David Griffiths Introduction to Electrodynamics, p 157

#     .. note::
#         The dipole calculation can be directly converted in Cartesian because it is simple
#     """

#     # p_bar = p - Q * a_bar
#     # where p is is the original dipole, Q is the charge of the molecule and a is the displacement amount
#     # the displacement is the new_origin - old_origin
#     # p_bar is the new dipole
#     # if the total charge is 0, then the dipole does not change with the origin change

#     return dipole - (molecular_charge * (new_origin - old_origin))


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
