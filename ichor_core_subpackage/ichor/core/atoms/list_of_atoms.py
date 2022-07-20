from abc import abstractmethod, ABC
from pathlib import Path
from typing import List, Optional, Union, Callable
import numpy as np
from ichor.core.atoms.atoms import Atoms
from ichor.core.atoms.calculators import ALF, get_atom_alf_from_list_of_alfs

class ListOfAtoms(list, ABC):
    """Used to focus only on how one atom moves in a trajectory, so the user can do something
     like trajectory['C1'] where trajectory is an instance of class Trajectory. This way the
    user can also do trajectory['C1'].features, trajectory['C1'].coordinates, etc."""

    def __init__(self):
        list.__init__(self)

    def features(
        self,
        feature_calculator: Callable[..., np.ndarray],
        **kwargs
    )-> np.ndarray:
        """Return the ndarray of features. This is assumed to be either 2D or 3D array.
        If the dimensionality of the feature array is 3, the array is transposed to transform a
        (ntimestep, natom, nfeature) array into a (natom, ntimestep, nfeature) array so that
        all features for a single atom are easier to group.
        :rtype: `np.ndarray`
        :return:
            If the features for the whole trajectory are returned, the array has shape `n_atoms` x `n_timesteps` x `n_features`
            If the trajectory instance is indexed by str, the array has shape `n_timesteps` x `n_features`.
            If the trajectory instance is indexed by int, the array has shape `n_atoms` x `n_features`.
            If the trajectory instance is indexed by slice, the array has shape `n_atoms` x`slice` x `n_features`.
        """
        
        features = np.array([timestep.features(feature_calculator, **kwargs) for timestep in self])
        if features.ndim == 3:
            features = np.transpose(features, (1, 0, 2))
        return features

    def get_headings(self):
        """Helper function which makes the column headings for csv or excel files in which features are going to be saved."""
        
        natoms = self.natoms
        nfeatures = 3*natoms - 6 if natoms > 1 else 1
        
        if nfeatures == 1:
            return ["bond1"]
        
        headings = ["bond1", "bond2", "angle"]

        remaining_features = nfeatures - 3
        remaining_features = int(remaining_features / 3)  # each feature has r, theta, phi component

        for feat in range(remaining_features):
            headings += [f"r{feat+3}", f"theta{feat+3}", f"phi{feat+3}"]
            
        return headings

    def features_to_csv(
        self,
        feature_calculator: Callable[..., np.ndarray],
        fname: Optional[Union[str, Path]] = None,
        atom_names: Optional[List[str]] = None,
        **kwargs
    ):
        """Writes csv files containing features for every atom in the system. Optionally a list can be passed in to get csv files for only a subset of atoms

        :param feature_calculator: Calculator function to be used to calculate features
        :param fname: A string to be appended to the default csv file names. A .csv file is written out for every atom with default name `atom_name`_features.csv
            If an fname is given, the name becomes `fname`_`atom_name`_features.csv
        :param atom_names: A list of atom names for which to write csv files. If None, then write out the features for every atom in the system.
        :param **kwargs: key word arguments to be passed to the feature calculator function
        """
        import pandas as pd

        if isinstance(atom_names, str):
            atom_names = [atom_names]

        # whether to write csvs for all atoms or subset
        if atom_names is None:
            atom_names = self.atom_names

        for atom_name in atom_names:
            atom_features = self[atom_name].features(feature_calculator, **kwargs)
            df = pd.DataFrame(atom_features, columns=self.get_headings())
            if fname is None:
                df.to_csv(f"{atom_name}_features.csv")
            else:
                df.to_csv(f"{fname}_{atom_name}_features.csv")

    def features_to_excel(
        self,
        fname: Optional[Union[str, Path]] = Path("features_to_excel.xlsx"),
        atom_names: List[str] = None,
        feature_calculator: Union[ALF, Callable] = default_feature_calculator,
    ):
        """Writes out one excel file which contains a sheet with features for every atom in the system. Optionally a list of atom names can be
        passed in to only make sheets for certain atoms

        :param atom_names: A list of atom names for which to calculate features and write in excel spreadsheet
        """
        import pandas as pd

        fname = Path(fname)
        fname = fname.with_suffix(".xlsx")

        if isinstance(atom_names, str):
            atom_names = [atom_names]
        # whether to write excel sheets for all atoms or subset
        if atom_names is None:
            atom_names = self.atom_names

        dataframes = {}

        for atom_name in atom_names:
            atom_features = self[atom_name].features(feature_calculator)
            df = pd.DataFrame(atom_features, columns=self.get_headings())
            dataframes[atom_name] = df

        with pd.ExcelWriter(fname) as workbook:
            for atom_name, df in dataframes.items():
                df.columns = self.get_headings()
                df.to_excel(workbook, sheet_name=atom_name)

    def center_geometries_on_atom_and_write_xyz(
        self,
        feature_calculator: Callable,
        central_atom_name: str,
        fname: Optional[Union[str, Path]] = None,
        **kwargs
    ):
        """Centers all geometries (from a Trajectory of PointsDirectory instance) onto a central atom and then writes out a new
        xyz file with all geometries centered on that atom. This is essentially what the ALFVisualizier application (ALFi) does.
        The features for the central atom are calculated, after which they are converted back into xyz coordinates (thus all geometries)
        are now centered on the given central atom).

        :param feature_calculator: Function which calculates features
        :param central_atom_name: the name of the central atom to center all geometries on. Eg. `O1`
        :param fname: Optional file name in which to save the rotated geometries.
        :param **kwargs: Key word arguments to pass to calculator function
        """

        from ichor.core.atoms import Atom
        from ichor.core.files import Trajectory
        from ichor.core.files.trajectory import features_to_coordinates
        from ichor.core.units import AtomicDistance

        if central_atom_name not in self.atom_names:
            raise ValueError(
                f"Central atom name {central_atom_name} not found in atom names:{self.atom_names}."
            )

        if not fname:
            fname = f"{central_atom_name}_centered_geometries.xyz"
            fname = Path(fname)
        else:
            fname = Path(fname)
            fname = fname.with_suffix(".xyz")

        # calcultate features and convert to a new Trajectory object
        alf = self[0][central_atom_name].alf()
        # before, ordering is 0,1,2,3,4,5,...,etc.
        # after calculating the features and converting back, the order is going to be
        # central atom idx, x-axis atom index, xy-plane atom index, rest of atom indices
        n_atoms = self.natoms
        previous_atom_ordering = list(range(n_atoms))
        current_atom_ordering = alf + [
            i for i in range(n_atoms) if i not in alf
        ]
        # this will get the index that the atom was moved to after reordering.
        reverse_alf_ordering = [
            current_atom_ordering.index(num) for num in range(n_atoms)
        ]
        # order will always be central atom(0,0,0), x-axis atom, xy-plane atom, etc.
        xyz_array = features_to_coordinates(
            self[central_atom_name].features(feature_calculator, **kwargs)
        )
        # reverse the ordering, so that the rows are the same as before
        # can now use the atom names as they were read in in initial Trajectory/PointsDirectory instance.
        xyz_array[:, previous_atom_ordering, :] = xyz_array[
            :, reverse_alf_ordering, :
        ]
        trajectory = Trajectory(fname)

        for geometry in xyz_array:
            # initialize empty Atoms instance
            atoms = Atoms()
            for ty, atom_coord in zip(self.types_extended, geometry):
                # add Atom instances for every atom in the geometry to the Atoms instance
                atoms.add(
                    Atom(
                        ty,
                        atom_coord[0],
                        atom_coord[1],
                        atom_coord[2],
                        units=AtomicDistance.Bohr,
                    )
                )
            # Add the filled Atoms instance to the Trajectory instance and repeat for next geometry
            atoms = atoms.to_angstroms()
            trajectory.add(atoms)

        trajectory.write()

    @property
    @abstractmethod
    def types(self) -> List[str]:
        """Returns the atom elements for atoms, assumes each timesteps has the same atoms.
        Removes duplicates."""
        ...

    @property
    @abstractmethod
    def types_extended(self) -> List[str]:
        """Returns the atom elements for atoms, assumes each timesteps has the same atoms.
        Does not remove duplicates"""
        ...

    @property
    @abstractmethod
    def atom_names(self):
        """Return the atom names from the first timestep. Assumes that all timesteps have the same
        number of atoms/atom names."""
        ...
        
    @property
    @abstractmethod
    def natoms(self):
        """ Returns the number of atoms in the first timestep. Each timestep should have the same number of atoms."""
        ...

    @property
    @abstractmethod
    def coordinates(self) -> np.ndarray:
        """
        Returns:
            :type: `np.ndarray`
            the xyz coordinates of all atoms for all timesteps. Shape `n_timesteps` x `n_atoms` x `3`
        """
        ...

    @property
    @abstractmethod
    def connectivity(self) -> np.ndarray:
        """ Returns the connectivity matrix of the first timestep."""
        ...

    @property
    @abstractmethod
    def alf(self) -> ALF:
        """ Returns the atomic local frame for the first timestep."""
        ...

    @abstractmethod
    def coordinates_to_xyz(
        self, fname: Optional[Union[str, Path]] = Path("system_to_xyz.xyz"), step: Optional[int] = 1
    ):
        """write a new .xyz file that contains the timestep i, as well as the coordinates of the atoms
        for that timestep.

        :param fname: The file name to which to write the timesteps/coordinates
        :param step: Write coordinates for every n^th step. Default is 1, so writes coordinates for every step
        """
        ...

    def features_with_properties_to_csv(
        self,
        str_to_append_to_fname: Optional[
            str
        ] = "_features_with_properties.csv",
        atom_names: Optional[List[str]] = None,
        property_types: Optional[List[str]] = None,
        feature_calculator: Callable,
    ):
        """

        :param str_to_append_to_fname: a string that is appended to the default file name (which is `name_of_atom.csv`), defaults to None
        :param atom_names: A list of atom names for which to write out csv files with properties. If None, then writes out files for all
            atoms in the system, defaults to None
        :param property_types: A list of property names (iqa, multipole names) for which to write columns. If None, then writes out
            columns for all properties, defaults to None
        :raises TypeError: This method only works for PointsDirectory instances because it needs access to AIMALL information. Does not
            work for Trajectory instances.
        """

        import pandas as pd
        from ichor.core import constants
        from ichor.core.files import PointsDirectory

        if isinstance(atom_names, str):
            atom_names = [atom_names]
        elif atom_names is None:
            atom_names = self.atom_names

        if not isinstance(self, PointsDirectory):
            raise TypeError(
                "This method only works for PointsDirectory instances because it needs access to AIMALL output data."
            )

        # TODO: add dispersion later if we are going to make models for it separately
        if not property_types:
            property_types = ["iqa"] + constants.multipole_names

        for atom_name in atom_names:

            training_data = []
            features = self[atom_name].features(feature_calculator, **kwargs)

            for i, point in enumerate(self):
                properties = [
                    point[atom_name].get_property(ty) for ty in property_types
                ]
                training_data.append([*features[i], *properties])

            input_headers = [f"f{i+1}" for i in range(features.shape[-1])]
            output_headers = [f"{output}" for output in property_types]

            fname = atom_name + str_to_append_to_fname

            df = pd.DataFrame(
                training_data,
                columns=input_headers + output_headers,
                dtype=np.float64,
            )
            df.to_csv(fname, index=False)

    def iteratoms(self):
        """Returns a generator of AtomView instances for each atom stored in ListOfAtoms."""
        for atom in self.atom_names:
            yield self[atom]

    def __getitem__(
        self, item: Union[int, str]
    ) -> Union[Atoms, "ListOfAtoms"]:
        """Used when indexing a Trajectory instance by an integer, string, or slice."""

        # if ListOfAtoms instance is indexed by an integer or np.int64, then index as a list
        if isinstance(item, (int, np.int64)):
            return super().__getitem__(item)

        # if ListOfAtoms is indexed by a string, such as an atom name (eg. C1, H2, O3, H4, etc.)
        elif isinstance(item, str):

            class AtomView(self.__class__):
                """Class used to index a ListOfAtoms instance by an atom name (eg. C1, H2, etc.). This allows
                a user to get information (such as coordinates or features) for one atom.

                :param parent: An instance of a class that subclasses from ListOfAtoms
                :param atom: A string representing the name of an atom, e.g. 'C1', 'H2', etc.
                """

                def __init__(self, parent, atom):
                    list.__init__(self)
                    self.__dict__ = parent.__dict__.copy()
                    self._atom = atom
                    self._is_atom_view = True
                    self._super = parent

                    # this usually iterates over Atoms instances that are stored in a ListofAtoms instance and only adds the information for the
                    # specified atom. Thus AtomView is essentially a list of Atom instances for only one atom
                    # also iterates over PointDirectory instances because PointsDirectory subclasses from ListofAtoms
                    for element in parent:
                        a = element[atom]
                        self.append(a)

                @property
                def name(self):
                    """Returns the name of the atom, e.g. 'C1', 'H2', etc."""
                    return self._atom

                @property
                def atom_names(self):
                    """Returns a list of atom names, since the AtomView only stores information for one atom, this list has one element."""
                    return [self._atom]

                @property
                def types(self):
                    """Returns the types of atoms in the atom view. Since only one atom type is present, it returns a list with one element"""
                    return [self[0].type]

                def features(self, feature_calculator: Callable, **kwargs):
                    """Return the ndarray of features for only one atom, given an alf for that atom.
                    This is assumed to a 2D array of features for only one atom.

                    :param alf: A list of integers or a numpy array corresponding to the alf of one atom - The atom which the atom view is for.
                    :rtype: `np.ndarray`
                    :return: Тhe array has shape `n_timesteps` x `n_features`.
                    """

                    return np.array([atom.features(feature_calculator, **kwargs) for atom in self])

            if hasattr(self, "_is_atom_view"):
                return self
            return AtomView(self, item)

        # if ListOfAtoms is indexed by a slice e.g. [:50], [20:40], etc.
        elif isinstance(item, slice):

            class AtomSlice(self.__class__):
                def __init__(self, parent, sl):
                    self.__dict__ = parent.__dict__.copy()
                    self._is_atom_slice = True
                    list.__init__(self)

                    self.extend(list.__getitem__(parent, sl))

            return AtomSlice(self, item)
        
        elif isinstance(item, (list, np.ndarray)):

            class ListOfAtomsSlice(self.__class__):
                def __init__(self, parent, sl):
                    self.__dict__ = parent.__dict__.copy()
                    self._is_list_of_atoms_slice = True
                    list.__init__(self)

                    for i in sl:
                        self.append(list.__getitem__(parent, i))

            return ListOfAtomsSlice(self, item)

        # if indexing by something else that has not been programmed yet, should only be reached if not indexed by int, str, or slice
        raise TypeError(
            f"Cannot index type '{self.__class__.__name__}' with type '{type(item)}"
        )
