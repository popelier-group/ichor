import numpy as np
from ichor.core.models.reciprocal_fflux_derivatives import reciprocal_fflux_derivs_da_df
from ichor.core.atoms import ALF
from typing import List, Dict

def cartesian_derivatives_wrt_features_for_all_atoms(atoms: "Atoms", system_alf: List["ALF"], central_atom_idx) -> np.ndarray:
    """Returns a np array of shape n_features x (n_atomsx3), containing the derivative of
    atomic x,y,z coordinates with respect to the features (of a given central atom).

    Note that the atoms are ordered as A_0, A_x, A_xy, A_4, A_5, ..., A_N. Therefore, the
    Gaussian forces vector must also be made in this order, so that the derivatives match up,
    so that we can get convert Gaussian forces (dE/da where a is a global Cartesian coord)
    to forces (dE/df) where f are features (of a given central atom).

    For example, the the first column will contain the derivative of x-coordinate of the A_0 atom (the
    central ALF atom) with respect to the first feature. The second column will be
    the y-coordinate of A_0 with respect to the first feature.
    The last column will be the derivative of the z-coordinate of the A_N atom with respect to
    the last feature.

    Features are ordered as distance to x-axis atom, distance to xy-plane atom,
    angle between x-axis atom and xy-plane atom, distance to Nth atom, theta to Nth atom,
    phi to Nth atom.

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
    atom_names = atoms.atom_names
    natoms = len(atoms)

    force_columns = []
    non_local_atoms = [t for t in range(natoms) if t not in system_alf[central_atom_idx]]

    # loop over all atoms in the system and calculate n_features x 3 submatrix
    # matrix contains derivatives of Global cartesian coordinates for one atom wrt all features.

    # first three atoms that are central, x-axis, xy-plane
    for j in range(3):
        force = reciprocal_fflux_derivs_da_df(central_atom_idx, system_alf[central_atom_idx][j], atoms, system_alf)
        force_columns.append(force)
    # rest of atoms in molecule
    for non_local_atm in non_local_atoms:
        force = reciprocal_fflux_derivs_da_df(central_atom_idx, non_local_atm, atoms, system_alf)
        force_columns.append(force)

    # shape n_features x 3N where N is the number of atoms. Thus multiplied by the vector of 3N (the Gaussian forces)
    # should give an n_features x1 vector which is the dE_df where E is the total energy
    da_df_matrix = np.hstack(force_columns)

    # make sure that the constructed matrix is still

    return da_df_matrix

def gaussian_energy_derivatives_wrt_features(atoms: "Atoms", system_alf: List["ALF"], central_atom_idx, forces_array):
    """Returns a vector of shape n_features x 1, containing the negative derivatives of the
    Gaussian energy with respect to to features. Thus, this function converts the Cartesian forces
    calculated by Gaussian to "feature" forces.

    :param atoms: An Atoms instance containing the geometry for which to predict forces.
        Note that the ordering of the atoms matters, i.e. the index of the atoms in the Atoms instance
        must match the index of the model files.
    :param system_alf: The system alf as a list of `ALF` instances (the `ALF` instances are just a named tuple
        containing origin_idx, x-axis_idx, xy_plane_idx. It is 0-indexed.)
    :param central atom index: The index of the atom to be used as the central atom. Therefore,
    the features are going to be for this central atom. 
    :param forces_array: A np.ndarray of shape n_atoms x 3, containing the forces from Gaussian.
        This array is converted internally, so that the central atom is always the first row,
        the x-axis is always the second row, and the xy-plane is always the third row, followed
        by atoms described in r-theta-phi. The system alf that is given determines the conversion
    """

    # copy array so that original array is not altered unintentionally.
    copied_forces_array = forces_array.copy()
    natoms = len(atoms)

    # matrix containing derivatives of global cartesian coordinates of all atoms
    # with respect to features (of specified central atom with given alf).
    # shape is n_features x (n_atomsx3)
    da_df_matrix = cartesian_derivatives_wrt_features_for_all_atoms(atoms, system_alf, central_atom_idx)

    # the columns of the da_df matrix are ordered as follows:
    # First three cols are derivatives of central atom coordinates with respect to features (given central atom)
    # Second three cols are the derivatives of the x-axis atom coordinates with respect to features (given central atom)
    # Third three colds are the derivatives of xy-plane atom coords wrt to features (of given central atom)
    #  The next sets of 3 columns are for derivatives of cartesian coordinates of non-ALF atoms wrt to features (of given central atom).

    # original row indices
    original_row_indices = [i for i in range(natoms)]

    # contains indices of central atom, x-axis atom, xy-plane atom
    alf_atom_indices = list(system_alf[central_atom_idx])
    # contains all other atom indices not in the alf
    non_local_atom_indices = [t for t in range(natoms) if t not in system_alf[central_atom_idx]]
    # the correct order which the forces array should be in
    atom_indices_new_order = alf_atom_indices + non_local_atom_indices

    # swap rows of forces array
    copied_forces_array[[atom_indices_new_order, original_row_indices]] = copied_forces_array[[original_row_indices, atom_indices_new_order]]

    dE_df = np.matmul(da_df_matrix, copied_forces_array.flatten())

    return dE_df