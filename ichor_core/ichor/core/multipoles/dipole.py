from typing import List, Tuple, Union

import numpy as np

from ichor.core.common.constants import coulombbohr_to_debye
from ichor.core.multipoles.primed_functions import mu_prime

# links to papers relating to dipole moment origin change
# https://doi.org/10.1021/jp067922u
# The effects of hydrogen-bonding environment on the polarization and electronic properties of water molecules
# https://doi.org/10.1080/15533170701854189
# The Asymptotic Behavior of the Dipole and Quadrupole Moment of a Single Water Molecule from Gas Phase to
# Large Clusters: A QCT Analysis


def rotate_dipole(
    q10: float, q11c: float, q11s: float, C: np.ndarray
) -> Tuple[float, float, float]:
    """Converts dipole to Cartesian from spherical, after which
    it rotates it using the C matrix, after which the rotated dipole
    is converted back into spherical tensor formulation.

    :param q10: q10 component of dipole
    :param q11c: q11c component of dipole
    :param q11s: q11s component of dipole
    :param C: rotation matrix (typically the ALF C matrix, but can be any other)
    """

    # Global cartesian dipole moment d is a simple rearrangement of the spherical form
    d = dipole_spherical_to_cartesian(q10, q11c, q11s)
    # Rotation of 1D cartesian tensor from global to local frame
    rotated_d = dipole_rotate_cartesian(d, C)
    # Convert Local Cartesian to Local Spherical
    return dipole_cartesian_to_spherical(rotated_d)


def dipole_spherical_to_cartesian(q10: float, q11c: float, q11s: float) -> np.ndarray:
    """Converts the dipole moment from spherical tensor to Cartesian
    tensor formulation.

    :param q10: q10 component of dipole
    :param q11c: q11c component of dipole
    :param q11s: q11s component of dipole
    :return: 1-dimensional np.ndarray containing the converted dipole moment
    """
    return np.array([q11c, q11s, q10])


def dipole_cartesian_to_spherical(d: np.ndarray) -> Tuple[float, float, float]:
    """Converts the dipole moment from Cartesian tensor to spherical
    tensor formulation

    :param d: np.ndarray containing the Cartesian dipole
    :return: A tuple containing the q10, q11c, and q11s components
    """

    return d[2], d[0], d[1]


def pack_cartesian_dipole(d_x: float, d_y: float, d_z: float) -> np.ndarray:
    """Packs the three Cartesian dipole moment
    components into a 1-dimensional array

    :param d_x: The x component of the dipole
    :param d_y: The y component of the dipole
    :param d_z: The z component of the dipole
    :return: 1 dimensional np.ndarray representing the dipole moment
    """

    return np.array([d_x, d_y, d_z])


def unpack_cartesian_dipole(d: Union[list, np.ndarray]) -> Tuple[float, float, float]:
    """Unpacks the three Cartesian dipole moment from a 1-dimensional array
    into a tuple of the three separate components

    :param d: The 1-dimensional array representing the dipole moment
    """

    return d[0], d[1], d[2]


def dipole_rotate_cartesian(d: np.ndarray, C: np.ndarray) -> np.ndarray:
    """Rotates the dipole moment using a rotation matrix.

    :param d: The 1-dimensional Cartesian dipole moment
    :param C: The 2-dimensional 3x3 rotation matrix
    :return: The rotated Cartesian dipole moment
    """

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

    mu_alpha_disp = dipole[alpha] + mu_prime(alpha, displacement_vector) * monopole

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

    # must convert to Bohr
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

    atoms = gaussian_output.atoms

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
