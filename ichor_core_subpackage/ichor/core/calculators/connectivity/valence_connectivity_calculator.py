import numpy as np
from ichor.core.calculators.connectivity.distance_connectivity_calculator import (
    connectivity_calculator_distance,
)


def connectivity_calculator_valence(atoms: "Atoms") -> np.ndarray:
    """
    Calculates the connectivity matrix (showing which atoms are bonded as 1 and those that are not bonded as 0.
    It uses the Van Der Waals radius an Atom (see `Atom` class) to determine if atoms should be bonded or not.

    Args:
        :atoms: `Atoms` instance

    Returns:
        :type: `np.ndarray`
            The connectivity matrix between atoms of shape len(atoms) x len(atoms)

    .. note::

        This is a class method because the connectivity only needs to be calculated once per trajectory. The connectivity remains the same for all
        timesteps in a trajectory.
    """

    connectivity = connectivity_calculator_distance(atoms)

    for atom in atoms:
        while sum(connectivity[atom.i]) > atom.valence:
            connected_atoms = [i for i, c in enumerate(connectivity[atom.i]) if c == 1]
            incorrect_atom_idx = connected_atoms[
                np.argmax([atom.dist(atoms[i]) for i in connected_atoms])
            ]
            connectivity[atom.i, incorrect_atom_idx] = 0
            connectivity[incorrect_atom_idx, atom.i] = 0

    return connectivity
