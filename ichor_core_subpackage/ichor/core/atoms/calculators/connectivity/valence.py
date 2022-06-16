import numpy as np
from ichor.core.atoms.calculators.connectivity.distance import calculate_connectivity_distance


def calculate_connectivity_valence(atoms) -> np.ndarray:
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

    connectivity = calculate_connectivity_distance(atoms)

    for atom in atoms:
        while sum(connectivity[atom.i]) > atom.valence:
            connectivity[np.argmax([atom.dist(atoms[i]) for i in connectivity])] = 0
    
    return connectivity
