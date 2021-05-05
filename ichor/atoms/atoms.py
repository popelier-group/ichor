import itertools as it
import numpy as np
from ichor.atoms.atom import Atom
from ichor.calculators.connectivity_calculator import ConnectivityCalculator


class Atoms(list):
    """
    The Atoms class handles ONE timestep in the trajectory. It is mainly used to group together
    Atom objects that are in the same timestep. However, it is written in a way that any
    number of Atom instances can be grouped together if the user wants to do so.

    e.g. if we have a trajectory of methanol (6 atoms) with 1000 timesteps, we will have 1000 Atoms instances. Each
    of the Atoms instances will hold 6 instances of the Atom class.
    """

    def __init__(self, atoms=None):

        self._centred = False
        Atom._counter = it.count(1)
        if atoms is not None:
            self.add(atoms)

    def add(self, atom):
        """
        Add Atom instances for each atom in the timestep to the self._atoms list.
        Each coordinate line in the trajectory file (for one timestep) is added as a separate Atom instance.
        """
        if isinstance(atom, Atom):
            self.append(atom)
        elif isinstance(atom, str):
            self.add(Atom(atom))
        elif isinstance(atom, (list, Atoms)):
            for a in atom:
                self.add(a)

    @property
    def natoms(self) -> int:
        """
        Returns the number of atoms in a timestep. Since each timestep has the same number of atoms. This
        means the number of atoms in the system is returned.
        """
        return len(self)

    @property
    def names(self) -> list:
        """Return a list of atom names that are held in the instance of Atoms."""

        return [atom.name for atom in self]

    @property
    def types(self) -> list:
        """ Returns the atom elements for atoms, removes duplicates"""
        return list(set([atom.type for atom in self]))

    @property
    def types_extended(self) -> list:
        """ Returns the atom elements for all atoms, includes duplicates."""
        return list([atom.type for atom in self])

    @property
    def coordinates(self) -> np.ndarray:
        """ Returns an array that contains the coordiantes for each Atom isntance held in the Atoms instance. """
        return np.array([atom.coordinates for atom in self])

    @property
    def connectivity(self) -> np.ndarray:
        """Return the connectivity matrix (n_atoms x n_atoms) for the given Atoms instance.

        Returns:
            :type: `np.ndarray` of shape n_atoms x n_atoms
        """

        return ConnectivityCalculator.calculate_connectivity(self)

    def to_angstroms(self):
        """
        Convert the x, y, z coordiantes of all Atom instances held in an Atoms instance to angstroms
        """
        for atom in self:
            atom.to_angstroms()

    def to_bohr(self):
        """
        Convert the x, y, z coordiantes of all Atom instances held in an Atoms instance to bohr
        """
        for atom in self:
            atom.to_bohr()

    def centre(self, centre_atom=None):
        if isinstance(centre_atom, int):
            centre_atom = self[centre_atom]
        elif centre_atom is None:
            centre_atom = self.centroid

        for i, atom in enumerate(self):
            atom -= centre_atom

        self._centred = True

    def rotate(self, R):
        """Perform a rotation in 3D space with a matrix R. This rotates all atoms in the system the same amount.
        This method also changes the coordinates of the Atom instances held in the Atoms instance."""

        for atom in self:
            atom._coordinates = R.dot(atom._coordinates.T).T

    def _rmsd(self, other):
        dist = 0
        for iatom, jatom in zip(self, other):
            dist += iatom.sq_dist(jatom)
        return np.sqrt(dist / len(self))

    def rmsd(self, other):
        if not self._centred:
            self.centre()
        if not other._centred:
            other.centre()

        H = self.coordinates.T.dot(other.coordinates)

        V, S, W = np.linalg.svd(H)
        d = (np.linalg.det(V) * np.linalg.det(W)) < 0.0

        if d:
            S[-1] = -S[-1]
            V[:, -1] = -V[:, -1]

        R = np.dot(V, W)

        other.rotate(R)
        return self._rmsd(other)

    @property
    def centroid(self):
        coordinates = self.coordinates.T

        x = np.mean(coordinates[0])
        y = np.mean(coordinates[1])
        z = np.mean(coordinates[2])

        return Atom([x, y, z])

    @property
    def masses(self) -> list:
        """Returns a list of the masses of the Atom instances held in the Atoms instance."""
        return [atom.mass for atom in self]

    @property
    def alf(self):
        """Returns the Atomic Local Frame (ALF) for all Atom instances that are held in Atoms
        e.g. [[0,1,2],[1,0,2], [2,0,1]]
        """
        return np.array([atom.alf for atom in self])

    @property
    def features(self) -> np.ndarray:
        """Returns the features for this Atoms instance, corresponding to the features of each Atom instance held in this Atoms isinstance
        Features are calculated in the Atom class and concatenated to a 2d array here.

        The array shape is n_atoms x n_features (3*n_atoms - 6)

        Returns:
            :type: `np.ndarray` of shape n_atoms x n_features (3N-6)
                Return the feature matrix of this Atoms instance
        """

        return np.array([atom.features for atom in self])

    @property
    def features_dict(self) -> dict:
        """Returns the features in a dictionary for this Atoms instance, corresponding to the features of each Atom instance held in this Atoms isinstance
        Features are calculated in the Atom class and concatenated to a 2d array here.

        e.g. {"C1": np.array, "H2": np.array}
        """

        return {atom.name: atom.features for atom in self}

    def __len__(self) -> int:
        """ returns the length of `self._atoms` if len() is called on an Atoms instance"""
        return len(self._atoms)

    def __getitem__(self, item) -> Atom:
        """Dunder method used to index the Atoms isinstance.

        e.g. we can index a variable atoms (which is an instance of Atoms) as atoms[0], or as atoms["C1"].
        In the first case, atoms[0] will return the 0th element (an Atom instance) held in this Atoms isinstance
        In the second case, atoms["C1] will return the Atom instance corresponding to atom with name C1."""

        if isinstance(item, str):
            for atom in self:
                if item == atom.name:
                    return atom
            raise KeyError(f"'{item}' does not exist")
        return super().__getitem__(item)

    def __delitem__(self, i):
        """deletes an instance of Atom from the self._atoms list (index i) if del is called on an Atoms instance
        e.g. del atoms[0], where atoms is an Atoms instance will delete the 0th element.
        del atoms["C1"] will delete the Atom instance with the name attribute of 'C1'."""

        if not (isinstance(i, int) or isinstance(i, str)):

            raise TypeError(
                f"Index {i} has to be of type int. Currently index is type {type(i)}"
            )

        else:
            del self[i]

    def __str__(self):
        return "\n".join([str(atom) for atom in self])

    def __repr__(self):
        return str(self)

    def __sub__(self, other):
        for i, atom in enumerate(self):
            for jatom in other:
                if jatom == atom:
                    del self[i]
        return self

    def __bool__(self):
        return bool(self)

    # def __delitem__(self, i):
    #     """deletes an instance of Atom from the self._atoms list (index i) if del is called on an Atoms instance
    #     e.g. del atoms[0], where atoms is an Atoms instance will delete the 0th element in atoms._atoms"""

    #     if not isinstance(i, int):
    #         # TODO: make the Atoms class work as a dictionary as well
    #         # del self[self._atoms[i].index]
    #         raise TypeError(
    #             f"Index {i} has to be of type int. Currently index is type {type(i)}"
    #         )

    #     else:
    #         del self._atoms[i]

    # TODO: make the Atoms class work as a dictionary as well
    # elif isinstance(i, str):
    #     del self._atoms[self[i].index]
    #     del self[i]

    # def __getitem__(self, i: Union[int, str]) -> Atom:
    #     # TODO: fix this
    #     # if isinstance(i, INT):
    #     #     i = self.atoms.index(i.atom)

    #     if not (isinstance(i, int) or isinstance(i, str)):
    #         raise TypeError(
    #             f"Index {i} has to be of type int or str. Currently index is type {type(i)}"
    #         )

    #     if isinstance(i, int):

    #         return self._atoms[i]

    #     elif isinstance(i, str):
    #         for atom in self:
    #             if atom.name == i:
    #                 return self._atoms[i]
