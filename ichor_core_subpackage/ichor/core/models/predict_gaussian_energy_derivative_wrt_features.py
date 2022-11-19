import numpy as np
from ichor.core.models.reciprocal_fflux_derivatives import reciprocal_fflux_derivs_da_df
from ichor.core.atoms import ALF
from typing import List, Dict

def gaussian_derivatives_wrt_features_for_all_atoms(atoms: "Atoms", system_alf: List["ALF"], central_atom_idx) -> np.ndarray:
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