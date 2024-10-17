from typing import List, Tuple, Union

import numpy as np
from ichor.core.common import constants
from ichor.core.common.arith import kronecker_delta


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


def quadrupole_element_conversion(quadrupole_array: np.ndarray, current_ordering):
    """Converts between the two ways of reporting quadrupole moments, namely

      0: xx, yy, zz, xy, xz, yz    this is the ordering used by GAUSSIAN/ORCA
      and
      1: xx, xy, xz, yy, yz, zz

      where the 0 and 1 indicate the ordering index. The other ordering is going to be returned

    :param quadrupole_array: 1d unpacked quadrupole array
    :type ordering: either 0 or 1
    """

    if current_ordering == 0:
        return quadrupole_array[[0, 3, 4, 1, 5, 2]]

    elif current_ordering == 1:
        return quadrupole_array[[0, 3, 5, 1, 2, 4]]

    raise ValueError(
        f"Current ordering can be either 0 or 1, but it is {current_ordering}"
    )


def quadrupole_nontraceless_to_traceless(
    nontraceless_quadrupole_matrix: np.ndarray,
) -> np.ndarray:
    """Subtracts off a constant (the mean of the sum of the trace), which makes
    the quadrupole moment traceless (i.e. the new sum of the diagonal is 0.0)

    .. note::
        AIMAll already gives traceless moments, but Gaussian does not have
        traceless moments for higher order multipole moments (higher than
        quadrupole.)

    :param nontraceless_quadrupole_matrix: A 3x3 matrix containing the (packed) quadrupole moment
    :return: A 3x3 matrix containing the traceless quadrupole moment
    """

    arr_to_sub = np.zeros_like(nontraceless_quadrupole_matrix)
    tr_mean = np.diag(nontraceless_quadrupole_matrix).mean()

    for i in range(3):
        arr_to_sub[i, i] += tr_mean

    return nontraceless_quadrupole_matrix - arr_to_sub


def Theta_prime(alpha, beta, displacement_vector):

    k = kronecker_delta(alpha, beta)
    norm = np.linalg.norm(displacement_vector)

    aprime_alpha = displacement_vector[alpha]
    aprime_beta = displacement_vector[beta]

    return 0.5 * (3 * aprime_alpha * aprime_beta - norm**2 * k)


def quadrupole_one_term_general_expression(
    alpha: int,
    beta: int,
    displacement_vector: np.ndarray,
    monopole: float,
    dipole: np.ndarray,
    quadrupole: np.ndarray,
) -> float:
    """Origin change of one component of the quadrupole moment by a displacement vector

    :param alpha: 0, 1, or 2 for x, y, or z
    :param beta: 0, 1, or 2 for x, y, or z
    :param displacement_vector: np.ndarray containing x,y,z components of displacement vector
    :param monopole: monopole moment, float (charge of atom or system).
        Note that for AIMAll, the q00 in the AIMAll .int file does not have the nuclear charge added
        ichor automatically does that when parsing .int files.
    :param dipole: The atomic or molecular dipole moment
        np.ndarray containing x,y,z components of displacement vector (Cartesian)
    :param quadrupole: The atomic or molecular quadrupole moment
        (3x3) matrix in Cartesian coordinates
    :returns: The component of the quadrupole moment, as seen from the new origin
    """

    term2 = Theta_prime(alpha, beta, displacement_vector) * monopole
    term3 = 1.5 * (displacement_vector[alpha] * dipole[beta])
    term4 = 1.5 * (displacement_vector[beta] * dipole[alpha])
    term5 = (displacement_vector.dot(dipole)) * kronecker_delta(alpha, beta)

    return quadrupole[alpha, beta] + term2 + term3 + term4 - term5


def displace_quadrupole_cartesian(
    displacement_vector: np.ndarray,
    monopole: float,
    dipole: np.ndarray,
    quadrupole: np.ndarray,
):
    """Computes the full displaced quadrupole moment

    :param displacement_vector: Displacement vector
    :param monopole: monopole moment, float (charge of atom or system).
        Note that for AIMAll, the atomic q00 (monopole) in the AIMAll .int file
        does not have the nuclear charge added
        ichor automatically does that when parsing .int files.
    :param dipole: The atomic or molecular dipole moment
        np.ndarray containing x,y,z components of displacement vector (Cartesian
    :param quadrupole: The atomic or molecular quadrupole moment
        (3x3) matrix in Cartesian coordinates
    :return: np.ndarray of shape (3x3) containing displaced quadrupole moment
    """

    assert displacement_vector.shape == (3,)
    # check that arrays are packed multipole moments
    assert isinstance(monopole, float)
    assert dipole.shape == (3,)
    assert quadrupole.shape == (3, 3)

    res = np.zeros((3, 3))

    for i in range(3):
        for j in range(3):
            res[i, j] = quadrupole_one_term_general_expression(
                i,
                j,
                displacement_vector,
                monopole,
                dipole,
                quadrupole,
            )

    return res


def recover_molecular_quadrupole(
    atoms: Union["ichor.core.Atoms", List["Atoms"]],  # noqa F821
    ints_dir: "ichor.core.files.IntDirectory",  # noqa F821
    convert_to_debye_angstrom=True,
    convert_to_cartesian=True,
    include_prefactor=True,
):
    """
    Calculates the recovered MOLECULAR quadrupole moment from ATOMIC quadrupole moments from AIMAll,
    given a geometry (atoms) and an ints_directory, containing the AIMAll calculations for
    the given geometry.

    .. note::
        Assumes atomic multipole moment units are atomic units (Coulomb Bohr**2) because this is what AIMAll gives.

    .. note:
        There is a factor of (2/3) that must be included which is excluded from
        GAUSSIAN/ORCA etc. See Anthony Stone Theory of Intermolecular Forces p20-23.
        AIMAll obtains the true quadrupole moment.
        GAUSSIAN and ORCA have different definitions of the multipole moments, so this
        is why the prefactor is needed.

    :param atoms: an Atoms instance containing the system geometry
    :param ints_dir: an IntDirectory file instance, which wraps around an AIMAll output directory
    :param convert_to_debye: Whether or not to convert the final result to DebyeAngstrom (from au),
        default to True.
    :param convert_to_cartesian: Whether or not to convert the recovered molecular quadrupole from spherical
        to Cartesian, defaults to True.
    :param prefactor: Include the (2/3) prefactor. Useful to directly compare to Gaussian
    :returns: A numpy array containing the molecular quadrupole moment.
    """

    from ichor.core.multipoles.dipole import dipole_spherical_to_cartesian

    atoms = [a.to_bohr() for a in atoms]

    # Cartesian representation
    molecular_quadrupole = np.zeros((3, 3))

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

        dipole_packed = dipole_spherical_to_cartesian(q10, q11c, q11s)
        quadrupole_packed = quadrupole_spherical_to_cartesian(
            q20, q21c, q21s, q22c, q22s
        )

        displaced_atomic_quadrupole_cartesian = displace_quadrupole_cartesian(
            atom_coords, q00, dipole_packed, quadrupole_packed
        )

        molecular_quadrupole += displaced_atomic_quadrupole_cartesian

    if convert_to_debye_angstrom:
        molecular_quadrupole *= constants.coulombbhrsquared_to_debyeangstrom

    if include_prefactor:
        molecular_quadrupole = (2 / 3) * molecular_quadrupole

    if not convert_to_cartesian:
        return quadrupole_cartesian_to_spherical(molecular_quadrupole)

    return molecular_quadrupole


def get_gaussian_and_aimall_molecular_quadrupole(
    gaussian_output: "ichor.core.files.GaussianOutput",  # noqa F821
    ints_directory: "ichor.core.files.IntsDir",  # noqa: F821
    atom_names: list = None,
):
    """Gets the Gaussian quadrupole moment and converts it to traceless (still in Debye Angstrom^2)
    Also gets the AIMAll recovered molecule quadrupole moment from atomic ones.

    Returns a tuple of numpy arrays, where the first one is the
    Gaussian traceless 3x3 quadrupole moment (in Debye Angstrom)
    and the second one is the AIMAll recovered traceless 3x3
    quadrupole moment (also converted from au to Debye Angstrom)
    and with prefactor taken into account.

    This allows for direct comparison of AIMAll to Gaussian.

    :param gaussian_output: A Gaussian output file containing molecular
        multipole moments and geometry. The same geometry and level of theory
        must also be used in the AIMAll calculation.
    :param ints_directory: A IntsDirectory instance containing the
        AIMAll .int files for the same geometry that was used in Gaussian
    :param atom_names: Optional list of atom names, which represent a subset of
        the atoms. The atomic multipole moments for this subset of atoms will be summed
    :return: A tuple of 3x3 np.ndarrays, where the first is the Gaussian
        quadrupole moment and the second is the AIMAll recovered quadrupole moment.
    """

    # make sure we are in Bohr
    atoms = gaussian_output.atoms

    if atom_names:
        # ensure that the passed in atom names are a subset of the all of the atom names
        if not set(atom_names).issubset(set(atoms.names)):
            raise ValueError(
                f"The passed atom names : {atom_names} must be a subset of all the atom names {atoms.names}."
            )

        atoms = [i for i in atoms if i.name in atom_names]

    # in debye angstrom
    raw_gaussian_quadrupole = np.array(gaussian_output.molecular_quadrupole)
    # convert to xx, xy, xz, yy, yz, zz
    # because Gaussian uses a different ordering
    converted_gaussian_quadrupole = quadrupole_element_conversion(
        raw_gaussian_quadrupole, 0
    )
    # pack into 3x3 array
    packed_converted_gaussian_quadrupole = pack_cartesian_quadrupole(
        *converted_gaussian_quadrupole
    )
    # convert Gaussian to traceless because AIMAll moments are traceless
    traceless_gaussian_quadrupole = quadrupole_nontraceless_to_traceless(
        packed_converted_gaussian_quadrupole
    )
    # note that conversion factors are applied in the function by default
    aimall_recovered_molecular_quadrupole = recover_molecular_quadrupole(
        atoms, ints_directory
    )

    return traceless_gaussian_quadrupole, aimall_recovered_molecular_quadrupole


# For spherical equations for quadrupole look at
# The newer equations above are generalized, so use these instead
# https://doi.org/10.1021/jp067922u
# The effects of hydrogen-bonding environment on the polarization and electronic properties of water molecules
# https://doi.org/10.1080/15533170701854189
# The Asymptotic Behavior of the Dipole and Quadrupole Moment of a Single Water Molecule from Gas Phase to
# Large Clusters: A QCT Analysis
