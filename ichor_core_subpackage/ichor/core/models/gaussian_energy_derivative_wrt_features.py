import numpy as np
from ichor.core.models.calculate_fflux_derivatives import fflux_derivs_da_df_matrix
from ichor.core.atoms import ALF
from typing import List, Dict

def form_b_matrix(atoms: "Atoms", system_alf: List["ALF"], central_atom_idx) -> np.ndarray:
    """Returns a np array of shape n_features x (n_atomsx3), containing the derivative of
    features with respect to atomic x,y,z coordinates

    .. note::
        The columns of the b matrix are ordered in the same way as the ordering of the Atoms instance.
        They are NOT ordered as A_0, A_x, A_xy, non-alf atoms.
        This means the b_matrix can be directly used with Gaussian forces (which also have the 
        same ordering as the Atoms instance.)

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

    if natoms > 2:
    # first three atoms that are central, x-axis, xy-plane
        for j in range(natoms):
            da_df = fflux_derivs_da_df_matrix(central_atom_idx, j, atoms, system_alf)
            all_derivs.append(da_df)

    elif natoms == 2:
        for j in range(2):
            da_df = fflux_derivs_da_df_matrix(central_atom_idx, j, atoms, system_alf)
            all_derivs.append(da_df)

    # shape n_features x 3N where N is the number of atoms. Thus multiplied by the vector of 3N (the Gaussian forces)
    # should give an n_features x1 vector which is the dE_df where E is the total energy
    da_df = np.hstack(all_derivs)

    # make sure that the constructed matrix is still

    return da_df