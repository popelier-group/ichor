import itertools as it
import re
import numpy as np
from ichor import constants
from typing import Union
from ichor.calculators.feature_calculator import ALFFeatureCalculator


class Atom:

    """
    The Atom class is used for ONE atom in ONE timestep.

    e.g. If we have 1000 timesteps in the trajectory, with 6 atoms in each timestep,
    the we will have 6000 Atom instances in total.
    """

    _counter = it.count(1)

    def __init__(self, coordinate_line, parent=None):

        self._atom_type = None  # to be read in from coordinate line
        self._atom_number = next(
            Atom._counter
        )  # these are used for the actual names, eg. O1 H2 H3, so the atom_number starts at 1
        self._parent = parent  # we need the parent Atoms because we need to know what other atoms are in the system to calcualte ALF/features

        self._x = None
        self._y = None
        self._z = None

        self.read_input(coordinate_line)

        self._coordinates = np.array([self._x, self._x, self._x])
        self._properties = None

    def read_input(self, coordinate_line: Union[str, list, tuple]):
        """
        Reads in ONE line in the trajectory file contanining ONE atom's x, y, z position and stores this
        atom's x, y, z coordinates, as well as other information like atom type and others
        """

        if isinstance(coordinate_line, str):
            find_atom = coordinate_line.split()
            self._atom_type = find_atom[0]
            coordinate_line = next(
                re.finditer(
                    r"(\s*[+-]?\d+.\d+([Ee][+-]?\d+)?){3}", coordinate_line
                )
            ).group()
            coordinate_line = re.finditer(
                r"[+-]?\d+.\d+([Ee][+-]?\d+)?", coordinate_line
            )
            self._x = float(next(coordinate_line).group())
            self._y = float(next(coordinate_line).group())
            self._z = float(next(coordinate_line).group())
        elif isinstance(coordinate_line, Atom):
            self = coordinate_line
        elif isinstance(coordinate_line, (list, tuple)):
            if len(coordinate_line) == 3:
                self._atom_type = "H"
                self._x = float(coordinate_line[0])
                self._y = float(coordinate_line[1])
                self._z = float(coordinate_line[2])
            elif len(coordinate_line) == 4:
                self._atom_type = coordinate_line[0]
                self._x = float(coordinate_line[1])
                self._y = float(coordinate_line[2])
                self._z = float(coordinate_line[3])

    def to_angstroms(self):
        """Convert the coordiantes to Angstroms"""
        self._coordinates /= constants.ang2bohr

    def to_bohr(self):
        """Convert the coordiantes to Bohr"""
        self._coordinates *= constants.ang2bohr

    @property
    def name(self) -> str:
        """Returns the name of the Atom instance, which is later used to distinguish atoms when making GPR models.
        The number in the name starts at 1 (inclusive).
        e.g. O1"""
        return f"{self.atom_type}{self._atom_number}"

    @property
    def atom_type(self) -> str:
        """Returns the type (i.e. element) of the Atom instance."""
        return self._atom_type

    @property
    def atom_number(self) -> int:
        """Returns the integer assigned to the atom, calculated from the trajectory file. Indeces start at 1.
        This number is given to every atom in the trajectory, so atoms of the same type(element) can be distinguished."""
        return self._atom_number

    @property
    def num(self):
        """See `atom_number` method."""
        return self.atom_number

    @property
    def index(self) -> int:
        """Returns the index of the atom, if used in any arrays/list in Python."""
        return self.atom_number - 1

    @property
    def mass(self) -> float:
        """ Returns the mass of the atom"""
        return round(constants.type2mass[self.atom_type], 6)

    @property
    def radius(self):
        """ Returns the Van der Waals radius of the given Atom instance."""
        return round(constants.type2rad[self._atom_type], 2)

    @property
    def coordinates(self) -> np.ndarray:
        """Returns the x,y,z coordinates of the Atom instance in an np array."""
        return self.coordinates

    @property
    def x(self) -> np.float64:
        """Returns the x coordinate of the Atom instance."""
        return self._coordinates[0]

    @property
    def y(self) -> np.float64:
        """Returns the y coordinate of the Atom instance."""
        return self._coordinates[1]

    @property
    def z(self) -> np.float64:
        """Returns the z coordinate of the Atom instance."""
        return self._coordinates[2]

    @property
    def connectivity(self) -> np.ndarray:
        """Returns the 1D np.array corresponding to the connectivity of ONE Atom with respect to all other Atom instances that are held in an Atoms instance.
        This is only one row of the full connectivity matrix of the Atoms instance that is self._parent."""

        if not self._parent:
            raise TypeError(
                "Parent not defined. Atom needs to know about Atoms to calculate connectivity."
            )

        return self._parent.connectivity[self.index]

    @property
    def bonded_atoms(self) -> list:
        """Returns a list of Atom instances to which this Atom instance is connected

        Returns:
            :type: `list` of `Atom` instances
        """

        if not self._parent:
            raise TypeError(
                "Parent not defined. Atom needs to know about Atoms to calculate connectivity."
            )

        connectivity_matrix_row = self.connectivity
        bonded_atoms = [
            self._parent[connected_atom]
            for connected_atom in connectivity_matrix_row.nonzero()[0]
        ]
        return bonded_atoms

    @property
    def bonded_atoms_names(self) -> list:
        """Returns a list of the names of Atom instances to which this Atom instance is connected

        Returns:
            :type: `list` of `str`
        """

        if not self._parent:
            raise TypeError(
                "Parent not defined. Atom needs to know about Atoms to calculate connectivity."
            )

        connectivity_matrix_row = self.connectivity
        bonded_atoms_names = [
            self._parent[connected_atom].name
            for connected_atom in connectivity_matrix_row.nonzero()[0]
        ]
        return bonded_atoms_names

    @property
    def bonded_atoms_indeces(self) -> list:
        """Returns a list of Atom indeces to which this Atom instance is connected

        Returns:
            :type: `list` of `int`, coresponding to the Atom instances indeces, as used in python lists (starting at 0).
        """

        if not self._parent:
            raise TypeError(
                "Parent not defined. Atom needs to know about Atoms to calculate connectivity."
            )

        connectivity_matrix_row = self.connectivity
        bonded_atoms_indeces = [
            self._parent[connected_atom].index
            for connected_atom in connectivity_matrix_row.nonzero()[0]
        ]
        return bonded_atoms_indeces

    @property
    def alf(self) -> np.ndarray:
        """Returns a numpy array of the Atomic Local Frame (ALF). This ALF is ONLY for this Atom.

        e.g. If we have an Atoms instance for the water monomer, the ALF for the whole water monomer can be written as [[0,1,2], [1,0,2], [2,0,1]],
        while the ALF for the first atom only is [0,1,2]

        [0,1,2] contains the indeces for the central atom, x-axis atom, and xy-plane atom. These indeces start at 0 to index Python objects correctly.
        """

        if not self._parent:
            raise TypeError(
                "Parent not defined. Atom needs to know about Atoms to calculate connectivity."
            )

        return ALFFeatureCalculator.calculate_alf(self)

    @property
    def features(self) -> np.ndarray:
        """Returns a 1D 3N-6 np.ndarray of the features for the current Atom instance."""
        return ALFFeatureCalculator.calculate_features(self)

    @property
    def coordinates_string(self):
        width = str(16)
        precision = str(8)
        return f"{self.x:{width}.{precision}f}{self.y:{width}.{precision}f}{self.z:{width}.{precision}f}"

    @property
    def alf(self):
        alf = [self]
        if self.x_axis is not None:
            alf.append(self.x_axis)
        if self.xy_plane is not None:
            alf.append(self.xy_plane)
        return alf

    @property
    def alf_nums(self):
        return [atom.num for atom in self.alf]

    def __getattr__(self, attr):
        try:
            return self.__dict__[attr]
        except KeyError:
            try:
                return getattr(self.properties, attr)
            except AttributeError:
                raise AttributeError(f"Cannot find attribute '{attr}'")

    def __str__(self):
        return f"{self._atom_type:<3s}{self.coordinates_string}"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if type(other) == Atom:
            return self.atom_num == other.atom_num
        elif type(other) == int:
            return self.atom_num == other
        else:
            raise ValueError(
                f"Cannot compare type({type(other)}) with type({type(self)})"
            )

    def __hash__(self):
        return hash(str(self.num) + str(self.coordinates_string))

    def __sub__(self, other):
        self._coordinates - other._coordinates
        return self

    # @property
    # def bonds(self):
    #     from ichor.atoms.atoms import Atoms

    #     return Atoms(self._bonds)

    # @property
    # def bond_list(self):
    #     return [atom.atom_number - 1 for atom in self._bonds]

    # @property
    # def angle_list(self):
    #     return [atom.atom_number - 1 for atom in self._angles]

    # @property
    # def mass(self):
    #     return constants.type2mass[self._atom_type]

    # @property
    # def coordinates(self):
    #     return self._coordinates

    # @property
    # def atom_num(self):
    #     return f"{self._atom_type}{self.atom_number}"

    # @property
    # def atom_num_coordinates(self):
    #     return [self.atom_num] + self.coordinates

    # @property
    # def atom_coordinates(self):
    #     return [self.atom] + self.coordinates
