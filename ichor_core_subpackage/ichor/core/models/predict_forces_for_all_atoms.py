import numpy as np
from ichor.core.models.calculate_fflux_derivatives import fflux_derivs
from ichor.core.atoms import ALF
from typing import List, Dict

def predict_fflux_forces_for_all_atoms(atoms: "Atoms", models: "Models", system_alf: List["ALF"]) -> np.ndarray:
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

    atomic_forces_list = []

    # make sure the coords are in Bohr because forces are calculated per Bohr
    atoms = atoms.to_bohr()
    atom_names = atoms.atom_names
    natoms = len(atoms)

    # make sure the ordering of the models is the same as the sequence of atoms 
    models_list = []
    for atom_name in atom_names:
        for model in models:
            if model.atom_name == atom_name and model.prop == "iqa":
                models_list.append(model)

    for atm_idx in range(natoms):

        # forces exerted on atom atoms[atom_idx]
        local_forces = np.zeros(3)
        non_local_atoms = [t for t in range(natoms) if t not in system_alf[atm_idx]]

        # first three atoms that are central, x-axis, xy-plane
        for j in range(3):
            force = fflux_derivs(atm_idx, system_alf[atm_idx][j], atoms, system_alf, models_list[system_alf[atm_idx][j]])
            local_forces = local_forces - force
        # rest of atoms in molecule
        for non_local_atm in non_local_atoms:
            force = fflux_derivs(atm_idx, non_local_atm, atoms, system_alf, models_list[non_local_atm])
            local_forces = local_forces - force

        atomic_forces_list.append(local_forces)

    return np.array(atomic_forces_list)

def predict_fflux_forces_for_all_atoms_dict(atoms: "Atoms", models: "Models", system_alf: List["ALF"]) -> Dict[str, np.ndarray]:
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
    :return: A dictionary of key: atom_name, value: 1D np.ndarray containing the x,y,z forces on the atom.
    """
    atom_names = atoms.atom_names
    forces = predict_fflux_forces_for_all_atoms(atoms, models, system_alf)

    return dict(zip(atom_names, forces))