from typing import List

import numpy as np
from ichor.core.atoms import ALF, Atoms
from ichor.core.models.calculate_fflux_derivatives import fflux_derivs_da_df_matrix

# TODO: Add method that converts back to Cartesian coordinates.
# Note that the rows will be A_0, A_x, A_xy, non_alf atoms. So need to revert back to original rows
# so that it can be compared to Gaussian.


def form_b_matrix(
    atoms: Atoms, system_alf: List["ALF"], central_atom_idx  # noqa F821
) -> np.ndarray:
    r"""
    Returns a np array of shape ``n_features`` x ``n_atomsx3``, containing the derivative of
    features with respect to x,y,z coordiantes.

    .. math::

        B_{ij} = \frac{df_i}{dx_j}

    where the partial derivative of feature i :math:`f_i` wrt.
    partial derivative of global Cartesian :math:`x_j`.

    See the following papers for details:

    .. _link1: https://doi.org/10.1002/(SICI)1096-987X(19960115)17:1<49::AID-JCC5>3.0.CO;2-0
    .. _link2: https://doi.org/10.1063/1.462844

    Using redundant internal coordinates to optimize equilibrium geometries and transition states:

    `link1`_

    Geometry optimization in redundant internal coordinates:

    `link2`_

    The first three columns of the B\-matrix are for atom :math:`A_0`.

    :math:`\frac{df_i}{dA^0_x}, \frac{df_i}{dA^0_y}, \frac{df_i}{dA^0_z}`

    The next three columns of the B\-matrix are for atom :math:`A_x`.

    :math:`\frac{df_i}{dA^x_x}, \frac{df_i}{dA^x_y}, \frac{df_i}{dA^x_z}`

    The next three columns of the B\-matrix are for atom :math:`A^{xy}`.

    :math:`\frac{df_i}{dA^{xy}_x}, \frac{df_i}{dA^{xy}_y}, \frac{df_i}{dA^{xy}_z}`

    The subsequent sets of three columns of the B\-matrix are for atom :math:`A^n`.
    which are atoms described by r, theta, phi.

    :math:`\frac{df_i}{dA^n_x}, \frac{df_i}{dA^n_y}, \frac{df_i}{dA^n_z}`

    .. note::
        The atoms instance is converted to Bohr internally because the forces are per Bohr in FFLUX.
        Also the `system_alf` argument is 0-indexed (as calculated by ichor methods),
        while the ALF in the .model files is 1-indexed.

    .. note::
        The ordering of the rows (corresponding to 3N-6 features) is going to depend on the ALF
        that is chosen for the atom. A different ALF would mean that a different set of features
        is defined, which will have different values and a different ordering of the features to
        which the atoms correspond to.

        The ordering of the columns (corresponding to 3N Cartesian coordinates) is always is the
        original ordering corresponding to the Atoms instance that is passed in. This ensures that
        the correct ordering is used when converting to feature forces.

    :param atoms: The Atoms instance for which to calculate the Wilson B matrix.
        The B matrix is calculated from the coordinates of the atoms.
    :param system_alf: The system alf as a list of `ALF` instances (the `ALF` instances are just a named tuple
        containing origin_idx, x-axis_idx, xy_plane_idx. It is 0-indexed.)
    :param central atom index: The index of the atom to be used as the central atom. Therefore,
        the derivatives df_i / dx_j are going to be for the features of this atom.
    """

    # make sure the coords are in Bohr because forces are calculated per Bohr
    atoms = atoms.to_bohr()
    natoms = len(atoms)

    # loop over all atoms in the system and calculate n_features x 3 submatrix
    # matrix contains derivatives of Global cartesian coordinates for one atom wrt all features.

    if natoms == 2:
        b_matrix = np.zeros((1, 6))
        for j in range(2):
            da_df = fflux_derivs_da_df_matrix(
                central_atom_idx, system_alf[central_atom_idx][j], atoms, system_alf
            )
            # fill in the three columns corresponding to df_i / dx_j for the specific atom
            # this way ensures that the original ordering of the atoms is preserved in the B matrix
            b_matrix[
                :,
                [
                    3 * system_alf[central_atom_idx][j],
                    3 * system_alf[central_atom_idx][j] + 1,
                    3 * system_alf[central_atom_idx][j] + 2,
                ],
            ] = da_df

    elif natoms > 2:
        # first three atoms that are central, x-axis, xy-plane
        nfeatures = 3 * natoms - 6
        b_matrix = np.zeros((nfeatures, 3 * natoms))
        for j in range(3):
            da_df = fflux_derivs_da_df_matrix(
                central_atom_idx, system_alf[central_atom_idx][j], atoms, system_alf
            )
            # fill in the three columns corresponding to df_i / dx_j for the specific atom
            # this way ensures that the original ordering of the atoms is preserved in the B matrix
            b_matrix[
                :,
                [
                    3 * system_alf[central_atom_idx][j],
                    3 * system_alf[central_atom_idx][j] + 1,
                    3 * system_alf[central_atom_idx][j] + 2,
                ],
            ] = da_df

        non_local_atoms = [
            t for t in range(natoms) if t not in system_alf[central_atom_idx]
        ]

        for non_local_atm in non_local_atoms:
            da_df = fflux_derivs_da_df_matrix(
                central_atom_idx, non_local_atm, atoms, system_alf
            )
            # fill in the three columns corresponding to df_i / dx_j for the specific atom
            # this way ensures that the original ordering of the atoms is preserved in the B matrix
            b_matrix[
                :, [3 * non_local_atm, 3 * non_local_atm + 1, 3 * non_local_atm + 2]
            ] = da_df

    # return B matrix
    return b_matrix


def b_matrix_true_finite_differences(atoms, system_alf, central_atom_idx=0, h=1e-6):
    """Computes the analytical and finite differences B matrix

    :param atoms: An atoms instance containing the geometry for which
        to calculate the B matrix
    :param central_atom_idx: The atom index for which to calculate a B matrix
        calculates the df_i / dc_j where f is the features of the central atom
    :param h: The finite difference to add to the Cartesian coordinates
        before calculating the features, defaults to 1e-6

    returns: A tuple of the analytical and finite differences B matrix

    .. note::
        The ordering of the columns (corresponding to 3N Cartesian coordinates) is always is the
        original ordering corresponding to the Atoms instance that is passed in. This ensures that
        the correct ordering is used when converting to feature forces.
    """
    from ichor.core.calculators import default_feature_calculator

    atoms = atoms.to_bohr()
    natoms = len(atoms)

    analytical = form_b_matrix(atoms, system_alf, central_atom_idx)
    finite_differences = np.zeros_like(analytical)
    for i in range(natoms):
        for j in range(3):

            atoms1 = atoms.copy()
            atoms2 = atoms.copy()

            atoms1[i].coordinates[j] += h
            atoms2[i].coordinates[j] -= h

            # get features for atoms with added coord
            features_plus_h = atoms1[central_atom_idx].features(
                default_feature_calculator, system_alf
            )
            # get features for atoms with subtracted coord
            features_minus_h = atoms2[central_atom_idx].features(
                default_feature_calculator, system_alf
            )

            # this should be df_i / dc_j for all features (i.e. should be a column)
            # of the B matrix
            numerical_deriv = (features_plus_h - features_minus_h) / (2 * h)

            # write to corresponding column
            # the i*3 + j gives 0 to (3*natoms) - 1
            # so writing a column at a time..
            finite_differences[:, (i * 3) + j] = numerical_deriv

    return analytical, finite_differences


def form_g_matrix(b_matrix: np.ndarray):
    """Forms the G matrix as in Gaussian.

    .. note::
        G is a symmetric square (BuB^T, where u is the identity matrix here))
    """

    return b_matrix @ b_matrix.T


def form_g_inverse(g_matrix: np.ndarray):
    """Inverts the G matrix, gives generalized inverse"""

    # using the generalized inverse seems to mess up results
    # there is some sort of roundoff error
    # happening as decomposition of G = V L V^T where L has eigenvalues on diagonal
    # but doing V L V^T does not give the exact numbers that BB^T=G gives

    # Gaussian also uses SVD, do not use eigendecomposition in numpy because
    # that is not that stable

    # can use pseudo inverse instead of finding G and G inverse
    U, S, V = np.linalg.svd(g_matrix)
    g_inv = V.T @ np.diag(S**-1) @ U.T

    return g_inv


def convert_to_feature_forces(global_cartesian_forces: np.ndarray, b_matrix):
    """
    Compute -dE/df (since the global Cartesian forces are negative of the derivative of the potential).
    If making models with these values, need to take the NEGATIVE of -dE/df, as the
    derivative of the potential energy is dE/df.

    dE/df are the values that need to be used when adding derivatives to GP model.

    :param global_cartesian_forces: A 2D numpy array of shape (N_atoms, 3) containing the global Cartesian forces.
    :param b_matrix: Wilson B matrix to be used to calculate, as well as dE/df. Should be of shape
        (3N-6) x 3N where N is the number of atoms.
    :param system_alf: A list of ALF instances containing the ALF of every atom.
    :param central_atom_idx: The index of the atom (0-indexed) which was the central ALF atom for which
        features (and feature derivatives) were calculated.

    .. note::
        The ordering of the forces should match up with the ordering of the B matrix.
        The 3N-6 rows of the B matrix correspond to the feature indices of the atom
        The 3N columns of the B matrix correspond to the x,y,z coordinates of each atom,
            where the ordering of the atoms is exactly the same as what is used to calculate
            the B matrix.

    See Using Redundant Internal Coordinates to Optimize Equilibrium Geometries and Transition States
    https://doi.org/10.1002/(SICI)1096-987X(19960115)17:1<49::AID-JCC5>3.0.CO;2-0
    https://doi.org/10.1063/1.462844
    """

    g_matrix = form_g_matrix(b_matrix)
    # can use np.linalg.pinv here as well
    g_inv = form_g_inverse(g_matrix)

    # note that if the forces are passed in, will get the
    # feature forces, which are the -ve of the gradient
    # the gradient is what is used for models
    feature_forces = g_inv @ b_matrix @ global_cartesian_forces.flatten()

    return feature_forces


def convert_to_cartesian_forces(
    dE_df_array: np.ndarray,
    b_matrix: np.ndarray,
):
    """Converts from local 'feature' forces to global Cartesian forces, as given by Gaussian.

    :param dE_df_array: 1D array of shape n_features x 1 containing 'feature' forces.
    :param b_matrix: Wilson B matrix to be used to calculate, as well as dE/df. Should be of shape
        (3N-6) x 3N where N is the number of atoms.
    :param system_alf: A list of ALF instances containing the ALF of every atom.
    :param central_atom_idx: The index of the atom (0-indexed) which was the central ALF atom for which
        features (and feature derivatives) were calculated.
    """

    # add a dimension if necessary, so that it is n_features x 1. This is needed when you
    # only have 1 feature (i.e. the input dE_df_array is a float)
    if dE_df_array.ndim == 0:
        dE_df_array = dE_df_array[..., np.newaxis]

    # form a N_atoms x 3 Cartesian Forces array
    dE_dCart = np.matmul(b_matrix.T, dE_df_array).reshape(-1, 3)

    return dE_dCart
