import numpy as np
from ichor.core.models.calculate_fflux_derivatives import fflux_derivs_da_df_matrix
from ichor.core.atoms import ALF
from typing import List, Dict

def form_b_matrix(atoms: "Atoms", system_alf: List["ALF"], central_atom_idx) -> np.ndarray:
    """Returns a np array of shape n_features x (n_atomsx3), containing the derivative of
    features with respect to atomic x,y,z coordinates

    See Using Redundant Internal Coordinates to Optimize Equilibrium Geometries and Transition States
    https://doi.org/10.1002/(SICI)1096-987X(19960115)17:1<49::AID-JCC5>3.0.CO;2-0
    https://doi.org/10.1063/1.462844

    .. note::
        The atoms instance is converted to Bohr internally because the forces are per Bohr in FFLUX.
        Also the `system_alf` argument is 0-indexed (as calcualted by ichor methods),
        while the ALF in the .model files is 1-indexed.

    :param atoms: An Atoms instance containing the geometry for which to predict forces.
        Note that the ordering of the atoms matters, i.e. the index of the atoms in the Atoms instance
        must match the index of the model files.
    :param system_alf: The system alf as a list of `ALF` instances (the `ALF` instances are just a named tuple
        containing origin_idx, x-axis_idx, xy_plane_idx. It is 0-indexed.)
    :param central atom index: The index of the atom to be used as the central atom. Therefore,
    the features are going to be for this central atom. 
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

def convert_to_feature_forces(global_cartesian_forces: np.ndarray, b_matrix, atoms, system_alf, central_atom_idx):
    """
    Compute -dE/df (since the global Cartesian forces are negative of the derivative of the potential)

    :param global_cartesian_forces: A 2D numpy array of shape (N_atoms, 3) containing the global Cartesian forces
    :param b_matrix: B matrix to be used to calculate G matrix, as well as dE/df

    .. note::
        The ordering of the forces should match up with the ordering of the b_matrix.

    .. note::
        The general inverse of G is NOT used here. Gaussian seems to use the regular inverse (so this is why np.linalg.inv is used,
        but can use Chloesky or something like this instead because G is a symmetric square (BuB^T, where u is the identity matrix here))
        Using the general inverse gives different results than Gaussian.

    See Using Redundant Internal Coordinates to Optimize Equilibrium Geometries and Transition States
    https://doi.org/10.1002/(SICI)1096-987X(19960115)17:1<49::AID-JCC5>3.0.CO;2-0
    https://doi.org/10.1063/1.462844
    """

    # copy array so that original array is not altered unintentionally.
    copied_forces_array = global_cartesian_forces.copy()
    natoms = len(atoms)

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

    g_matrix = np.matmul(b_matrix, b_matrix.T)
    # w is eigenvalues, v is eigenvectors matrix
    w, v = np.linalg.eig(g_matrix)

    # swap rows of forces array
    copied_forces_array[[atom_indices_new_order, original_row_indices]] = copied_forces_array[[original_row_indices, atom_indices_new_order]]
    copied_forces_array = copied_forces_array.flatten()

    # inverse_eigenvalues = w**-1
    # inverse_eigenvalues_diagonal_matrix = inverse_eigenvalues * np.eye(len(w))
    # generalized_g_inverse = np.matmul(v, np.matmul(inverse_g, v.T))
    # gradient_dE_dq = np.matmul(inverse_g, np.matmul(generalized_g_inverse, copied_forces_array))

    inverse_g = np.linalg.inv(g_matrix)

    gradient_dE_dq = np.matmul(inverse_g, np.matmul(b_matrix, copied_forces_array))

    return gradient_dE_dq
