import numpy as np


class ConnectivityCalculator:

    connectivity = None

    @classmethod
    def calculate_connectivity(cls, atoms):
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

        if cls.connectivity is None:

            connectivity = np.zeros((len(atoms), len(atoms)))

            for i, iatom in enumerate(atoms):
                for j, jatom in enumerate(atoms):
                    if iatom != jatom:
                        max_dist = 1.2 * (iatom.radius + jatom.radius)
                        if (
                            np.linalg.norm(
                                iatom.coordinates - jatom.coordinates
                            )
                            < max_dist
                        ):
                            connectivity[i, j] = 1

            cls.connectivity = connectivity

        return cls.connectivity
