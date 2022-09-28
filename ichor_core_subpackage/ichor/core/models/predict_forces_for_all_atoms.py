from ichor.core.files import XYZ
from ichor.core.models.model import Model
import numpy as np
from ichor.core.models.calculate_fflux_derivatives import fflux_derivs
from ichor.core.atoms import ALF
from typing import List

def predict_fflux_forces_for_all_atoms(atoms: "Atoms", models: "Models", system_alf: List["ALF"]):

    atomic_forces_list = []

    # make sure the coords are in Bohr because forces are calculated per Bohr
    atoms = atoms.to_bohr()
    atom_names = atoms.atom_names
    natoms = len(atoms)

    # make sure the ordering of the models is the same as the sequence of atoms 
    models_list = []
    for atom_name in atom_names:
        models_list.append(models[atom_name])

    for atm_idx in range(natoms):

        local_forces = np.zeros(3)
        non_local_atoms = [t for t in range(natoms) if t not in system_alf[atm_idx]]

        # first three atoms that are central, x-axis, xy-plane
        for j in range(3):
            force = fflux_derivs(atm_idx, system_alf[atm_idx][j], atoms, system_alf, models[system_alf[atm_idx][j]])
            local_forces = local_forces - force
        # rest of atoms in molecule
        for non_local_atm in non_local_atoms:
            force = fflux_derivs(atm_idx, non_local_atm, atoms, system_alf, models[non_local_atm])
            local_forces = local_forces - force

        atomic_forces_list.append(local_forces)

    return np.array(atomic_forces_list)
    