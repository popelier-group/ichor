import numpy as np


def connectivity_calculator_distance(atoms: "Atoms") -> np.ndarray:
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

    atoms = atoms.to_angstroms()
    natoms = atoms.natoms

    connectivity = np.zeros((natoms, natoms), dtype=int)

    for i, iatom in enumerate(atoms):
        for j, jatom in enumerate(atoms):
            if iatom != jatom:
                max_dist = 1.25 * (iatom.radius + jatom.radius)

                if iatom.dist(jatom) < max_dist:
                    connectivity[i, j] = 1

    return connectivity
