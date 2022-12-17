import numpy as np
from ichor.core.models.calculate_fflux_derivatives import fflux_derivs_da_df_matrix
from ichor.core.atoms import ALF
from typing import List, Dict

# TODO: Add method that converts back to Cartesian coordinates. Note that the rows will be A_0, A_x, A_xy, non_alf atoms. So need to revert back to original rows
# so that it can be compared to Gaussian.

def form_b_matrix(atoms: "Atoms", system_alf: List["ALF"], central_atom_idx) -> np.ndarray:
    """Returns a np array of shape n_features x (n_atomsx3), containing the derivative of
    features with respect to x,y,z coordiantes. B_{ij} = df_i / dx_j (the partial derivative of
    feature i wrt partial derivative of global Cartesian x_j).

    See Using Redundant Internal Coordinates to Optimize Equilibrium Geometries and Transition States
    https://doi.org/10.1002/(SICI)1096-987X(19960115)17:1<49::AID-JCC5>3.0.CO;2-0
    https://doi.org/10.1063/1.462844

    .. note::
        The first three columns of the B-matrix are for atom A_0 (df_i / dA0_x, df_i / dA0_y, df_i / dA0_z)
        The next three columns of the B-matrix are for atom A_x (df_i / dAx_x, df_i / dAx_y, df_i / dx_z)
        The next three columns of the B-matrix are for atom Axy (df_i / dAxy_x, df_i / dAxy_y, df_i / dAxy_z)
        The subsequents sets of three columns of the B-matrix are for atom An, atoms described
            by r, theta, phi (df_i / dAn_x, df_i / dAn_y, df_i / dAn_z)

    .. note::
        The atoms instance is converted to Bohr internally because the forces are per Bohr in FFLUX.
        Also the `system_alf` argument is 0-indexed (as calculated by ichor methods),
        while the ALF in the .model files is 1-indexed.

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

    all_derivs = []

    # loop over all atoms in the system and calculate n_features x 3 submatrix
    # matrix contains derivatives of Global cartesian coordinates for one atom wrt all features.

    if natoms == 2:
        for j in range(2):
            da_df = fflux_derivs_da_df_matrix(central_atom_idx, system_alf[central_atom_idx][j], atoms, system_alf)
            all_derivs.append(da_df)

    elif natoms > 2:
    # first three atoms that are central, x-axis, xy-plane
        for j in range(3):
            da_df = fflux_derivs_da_df_matrix(central_atom_idx, system_alf[central_atom_idx][j], atoms, system_alf)
            all_derivs.append(da_df)

        non_local_atoms = [t for t in range(natoms) if t not in system_alf[central_atom_idx]]

        for non_local_atm in non_local_atoms:
            da_df = fflux_derivs_da_df_matrix(central_atom_idx, non_local_atm, atoms, system_alf)
            all_derivs.append(da_df)

    da_df = np.hstack(all_derivs)

    # return B matrix
    return da_df

def form_g_matrix(b_matrix: np.ndarray):
    """ Forms and inverts the G matrix as in Gaussian.

    .. note::
        The general inverse of G is NOT used here. Gaussian seems to use the regular inverse (so this is why np.linalg.inv is used,
        but can use Chloesky or something like this instead because G is a symmetric square (BuB^T, where u is the identity matrix here))
        Using the general inverse gives different results than Gaussian.    
    """

    g_matrix = np.matmul(b_matrix, b_matrix.T)
    # w is eigenvalues, v is eigenvectors matrix
    w, v = np.linalg.eig(g_matrix)

    inverse_g = np.linalg.inv(g_matrix)

    # Gaussian does not seem to do a generalized inverse
    # inverse_eigenvalues = w**-1
    # inverse_eigenvalues_diagonal_matrix = inverse_eigenvalues * np.eye(len(w))
    # generalized_g_inverse = np.matmul(v, np.matmul(inverse_g, v.T))

    return inverse_g

def convert_to_feature_forces(global_cartesian_forces: np.ndarray, b_matrix, system_alf, central_atom_idx):
    """
    Compute -dE/df (since the global Cartesian forces are negative of the derivative of the potential).
    If making models with these values, need to take the NEGATIVE of -dE/df, as the
    derivative of the potential energy is dE/df. dE/df are the values that need to be used when adding derivatives to GP model.

    :param global_cartesian_forces: A 2D numpy array of shape (N_atoms, 3) containing the global Cartesian forces.
        The rows of this array are swapped internally to match the rows of the b-matrix.
    :param b_matrix: Wilson B matrix to be used to calculate, as well as dE/df. Should be of shape
        (3N-6) x 3N where N is the number of atoms.
    :param system_alf: A list of ALF instances containing the ALF of every atom.
    :param central_atom_idx: The index of the atom (0-indexed) which was the central ALF atom for which
        features (and feature derivatives) were calculated.

    .. note::
        The ordering of the forces should match up with the ordering of the b_matrix.

    See Using Redundant Internal Coordinates to Optimize Equilibrium Geometries and Transition States
    https://doi.org/10.1002/(SICI)1096-987X(19960115)17:1<49::AID-JCC5>3.0.CO;2-0
    https://doi.org/10.1063/1.462844
    """

    # copy array so that original array is not altered unintentionally.
    copied_forces_array = global_cartesian_forces.copy()
    natoms = global_cartesian_forces.shape[0]

    # original row indices
    original_row_indices = [i for i in range(natoms)]

    # contains indices of central atom, x-axis atom, xy-plane atom
    alf_atom_indices = list(system_alf[central_atom_idx])
    if None in alf_atom_indices:
        alf_atom_indices.remove(None)

    # contains all other atom indices not in the alf
    non_local_atom_indices = [t for t in range(natoms) if t not in system_alf[central_atom_idx]]
    # the correct order which the forces array should be in
    atom_indices_new_order = alf_atom_indices + non_local_atom_indices

    # swap rows of forces array
    copied_forces_array[[atom_indices_new_order, original_row_indices], :] = copied_forces_array[[original_row_indices, atom_indices_new_order], :]
    copied_forces_array = copied_forces_array.flatten()

    inverse_g = form_g_matrix(b_matrix)

    gradient_dE_df = np.matmul(inverse_g, np.matmul(b_matrix, copied_forces_array))

    return gradient_dE_df

def convert_to_cartesian_forces(dE_df_array: np.ndarray, b_matrix: np.ndarray, system_alf: List[ALF], central_atom_idx: int):
    """ Converts from local 'feature' forces to global Cartesian forces, as given by Gaussian.

    :param dE_df_array: 1D array of shape n_features x 1 containing 'feature' forces.  
    :param b_matrix: Wilson B matrix to be used to calculate, as well as dE/df. Should be of shape
        (3N-6) x 3N where N is the number of atoms.
    :param system_alf: A list of ALF instances containing the ALF of every atom.
    :param central_atom_idx: The index of the atom (0-indexed) which was the central ALF atom for which
        features (and feature derivatives) were calculated.
    """

    natoms = len(system_alf)

    # original row indices
    original_row_indices = [i for i in range(natoms)]

    # contains indices of central atom, x-axis atom, xy-plane atom
    alf_atom_indices = list(system_alf[central_atom_idx])
    if None in alf_atom_indices:
        alf_atom_indices.remove(None)

    # contains all other atom indices not in the alf
    non_local_atom_indices = [t for t in range(natoms) if t not in system_alf[central_atom_idx]]
    # the correct order which the forces array should be in
    atom_indices_new_order = alf_atom_indices + non_local_atom_indices

    # form a N_atoms x 3 Cartesian Forces array
    dE_dCart = np.matmul(b_matrix.T, dE_df_array).reshape(-1, 3)

    # swap rows of Cartesian array to match the original Atoms ordering
    dE_dCart[[original_row_indices, atom_indices_new_order], :] = dE_dCart[[atom_indices_new_order, original_row_indices], :]

    return dE_dCart
