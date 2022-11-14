import numpy as np
from ichor.core.models.reciprocal_fflux_derivatives import reciprocal_fflux_derivs_da_df
from ichor.core.atoms import ALF
from typing import List, Dict

def predict_gaussian_derivatives_wrt_features_for_all_atoms(atoms: "Atoms", system_alf: List["ALF"], central_atom_idx) -> np.ndarray:
    """Predicts the forces that FFLUX predicts (which are written to IQA_FORCES file).

    .. note::
        The atoms instance is converted to Bohr internally because the forces are per Bohr in FFLUX.
        Also the `system_alf` argument is 0-indexed (as calcualted by ichor methods),
        while the ALF in the .model files is 1-indexed.

    :param atoms: An Atoms instance containing the geometry for which to predict forces.
        Note that the ordering of the atoms matters, i.e. the index of the atoms in the Atoms instance
        must match the index of the model files.
    :param models: A models instance which wraps around a directory containing model files.
    :param system_alf: The system alf as a list of `ALF` instances (the `ALF` instances are just a named tuple
        containing origin_idx, x-axis_idx, xy_plane_idx. It is 0-indexed.)
    :return: A np.ndarray of shape n_atoms x 3 containing the x,y,z force for every atom
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