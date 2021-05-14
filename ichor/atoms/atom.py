import itertools as it
from typing import Optional, Union

import numpy as np

from ichor import constants
from ichor.atoms.calculators import ALFFeatureCalculator
from ichor.units import AtomicDistance


class Atom:
    """
    The Atom class is used for ONE atom in ONE timestep.

    e.g. If we have 1000 timesteps in the trajectory, with 6 atoms in each timestep,
    the we will have 6000 Atom instances in total.
    """

    def __init__(
        self,
        ty: str,
        x: float,
        y: float,
        z: float,
        index: Optional[int] = None,
        parent: Optional["Atoms"] = None,
        units: AtomicDistance = AtomicDistance.Angstroms,
    ):
        # to be read in from coordinate line
        # element of atom
        self.type = ty
        # these are used for the actual names, eg. O1 H2 H3, so the atom_number starts at 1
        self.index = next(Atom._counter)
        # we need the parent Atoms because we need to know what other atoms are in the system to calcualte ALF/features
        self._parent = parent
        
        self.coordinates = np.array([x, y, z])

        self.units = units

        self._properties = None

    def to_angstroms(self):
        """Convert the coordiantes to Angstroms"""
        if self.units != AtomicDistance.Angstroms:
            self.coordinates *= constants.bohr2ang
            self.units = AtomicDistance.Angstroms

    def to_bohr(self):
        """Convert the coordiantes to Bohr"""
        if self.units != AtomicDistance.Bohr:
            self.coordinates *= constants.ang2bohr
            self.units = AtomicDistance.Bohr

    @property
    def parent(self) -> "Atoms":
        if self._parent is None:
            raise TypeError(f"'parent' is not defined for '{self.name}'")
        return self._parent

    @property
    def index(self) -> int:
        if self._index is None:
            raise TypeError(
                f"'index' is not defined for instance of '{self.type} ({self.x} {self.y} {self.z})'"
            )
        return self._index

    @index.setter
    def index(self, index: int) -> None:
        self._index = index

    @property
    def name(self) -> str:
        """Returns the name of the Atom instance, which is later used to distinguish atoms when making GPR models.
        The number in the name starts at 1 (inclusive).
        e.g. O1"""
        return f"{self.type}{self.index}"

    @property
    def x(self) -> np.float64:
        return self.coordinates[0]

    @property
    def y(self) -> np.float64:
        return self.coordinates[1]

    @property
    def z(self) -> np.float64:
        return self.coordinates[2]

    @property
    def atom_type(self) -> str:
        """Returns the type (i.e. element) of the Atom instance."""
        return self.type

    @property
    def atom_number(self) -> int:
        """Returns the integer assigned to the atom, calculated from the trajectory file. Indeces start at 1.
        This number is given to every atom in the trajectory, so atoms of the same type(element) can be distinguished."""
        return self.index

    @property
    def num(self):
        """See `atom_number` method."""
        return self.atom_number

    @property
    def i(self) -> int:
        """Returns the index of the atom, if used in any arrays/list in Python."""
        return self.index - 1

    @property
    def mass(self) -> float:
        """Returns the mass of the atom"""
        return round(constants.type2mass[self.atom_type], 6)

    @property
    def radius(self):
        """Returns the Van der Waals radius of the given Atom instance."""
        return round(constants.type2rad[self.type], 2)

    @property
    def connectivity(self) -> np.ndarray:
        """
        Returns the 1D np.array corresponding to the connectivity of ONE Atom with respect to all other Atom
        instances that are held in an Atoms instance.
        This is only one row of the full connectivity matrix of the Atoms instance that is self._parent.
        """
        return self.parent.connectivity[self.i]

    @property
    def bonded_atoms(self) -> list:
        """Returns a list of Atom instances to which this Atom instance is connected

        Returns:
            :type: `list` of `Atom` instances
        """
        connectivity_matrix_row = self.connectivity
        return [
            self.parent[connected_atom]
            for connected_atom in connectivity_matrix_row.nonzero()[0]
        ]

    @property
    def bonded_atoms_names(self) -> list:
        """Returns a list of the names of Atom instances to which this Atom instance is connected

        Returns:
            :type: `list` of `str`
        """
        connectivity_matrix_row = self.connectivity
        return [
            self.parent[connected_atom].name
            for connected_atom in connectivity_matrix_row.nonzero()[0]
        ]

    @property
    def bonded_atoms_i(self) -> list:
        """Returns a list of Atom indeces to which this Atom instance is connected

        Returns:
            :type: `list` of `int`, coresponding to the Atom instances indeces, as used in python lists (starting at 0).
        """
        connectivity_matrix_row = self.connectivity
        return [
            self.parent[connected_atom].i
            for connected_atom in connectivity_matrix_row.nonzero()[0]
        ]

    @property
    def alf(self) -> np.ndarray:
        """Returns a numpy array of the Atomic Local Frame (ALF). This ALF is ONLY for this Atom.

        e.g. If we have an Atoms instance for the water monomer, the ALF for the whole water monomer can be written as [[0,1,2], [1,0,2], [2,0,1]],
        while the ALF for the first atom only is [0,1,2]

        [0,1,2] contains the indeces for the central atom, x-axis atom, and xy-plane atom. These indeces start at 0 to index Python objects correctly.
        """
        return ALFFeatureCalculator.calculate_alf(self)

    @property
    def alf_i(self):
        """Returns a list containing the index of the central atom, the x-axis atom, and the xy-plane atom.
        THere indeces are what are used in python lists (as they start at 0)."""
        return [atom.i for atom in self.alf]

    @property
    def features(self) -> np.ndarray:
        """Returns a 1D 3N-6 np.ndarray of the features for the current Atom instance."""
        # print("here")
        # print(ALFFeatureCalculator.calculate_features(self))
        # quit()
        return ALFFeatureCalculator.calculate_features(self)

    @property
    def coordinates_string(self):
        width = str(16)
        precision = str(8)
        return f"{self.x:{width}.{precision}f}{self.y:{width}.{precision}f}{self.z:{width}.{precision}f}"

    def __str__(self):
        """ Print out the atom name (containing atom type and index as used in model making), as well as
        coordinates of the atom
        """
        return f"{self.name:<3s}{self.coordinates_string}"

    def __repr__(self):
        return str(self)

    def __eq__(self, other: Union["Atom", int]):
        """Check if """
        if isinstance(other, Atom):
            return self.index == other.index
        elif isinstance(other, int):
            return self.index == other
        else:
            raise ValueError(
                f"Cannot compare type({type(other)}) with type({type(self)})"
            )

    def __hash__(self):
        return hash(str(self.num) + str(self.coordinates_string))

    def __sub__(self, other):
        self.coordinates -= other.coordinates
        return self
