from pathlib import Path
from typing import List, Optional, Union

import numpy as np
from numpy.lib.arraysetops import isin


class ListOfAtoms(list):
    """Used to focus only on how one atom moves in a trajectory, so the user can do something
     like trajectory['C1'] where trajectory is an instance of class Trajectory. This way the
    user can also do trajectory['C1'].features, trajectory['C1'].coordinates, etc."""

    def __init__(self):
        list.__init__(self)

    @property
    def types(self) -> List[str]:
        """Returns the atom elements for atoms, assumes each timesteps has the same atoms.
        Removes duplicates."""
        
        from ichor.files import PointsDirectory, Trajectory
        
        if isinstance(self, PointsDirectory):
            return self[0].atoms.types
        elif isinstance(self, Trajectory):
            return self[0].types

    @property
    def types_extended(self) -> List[str]:
        """Returns the atom elements for atoms, assumes each timesteps has the same atoms.
        Does not remove duplicates"""
        
        from ichor.files import PointsDirectory, Trajectory
        
        if isinstance(self, PointsDirectory):
            return self[0].atoms.types_extended
        elif isinstance(self, Trajectory):
            return self[0].types

    @property
    def atom_names(self):
        """Return the atom names from the first timestep. Assumes that all timesteps have the same
        number of atoms/atom names."""
        
        from ichor.files import PointsDirectory, Trajectory
        
        if isinstance(self, PointsDirectory):
            return self[0].atoms.atom_names
        elif isinstance(self, Trajectory):
            return self[0].atom_names

    @property
    def coordinates(self) -> np.ndarray:
        """
        Returns:
            :type: `np.ndarray`
            the xyz coordinates of all atoms for all timesteps. Shape `n_timesteps` x `n_atoms` x `3`
        """
        from ichor.files import PointsDirectory, Trajectory
        
        if isinstance(self, PointsDirectory):
            return np.array([timestep.atoms.coordinates for timestep in self])
        elif isinstance(self, Trajectory):
            return np.array([timestep.coordinates for timestep in self])

    @property
    def connectivity(self) -> np.ndarray:
        
        from ichor.files import PointsDirectory, Trajectory
        
        if isinstance(self, PointsDirectory):
            return self[0].atoms.connectivity
        elif isinstance(self, Trajectory):
            return self[0].connectivity

    @property
    def alf(self) -> np.ndarray:

        from ichor.files import PointsDirectory, Trajectory
        
        if isinstance(self, PointsDirectory):
            return self[0].atoms.alf
        elif isinstance(self, Trajectory):
            return self[0].alf

    @property
    def features(self):
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
        features = np.array([i.features for i in self])
        if features.ndim == 3:
            features = np.transpose(features, (1, 0, 2))
        return features

    def alf_features(
        self, alf: Optional[Union[List[int], List["Atom"], np.ndarray]] = None
    ):
        """Return the ndarray of features. This is assumed to be either a 1D, 2D or 3D array.
        If the dimensionality of the feature array is 3, the array is transposed to transform a
        (natom, ntimestep, nfeature) array into a (ntimestep, natom, nfeature) array so that
        all features for a single timestep are easier to group.
        :rtype: `np.ndarray`
        :return:
            A 3D array of features for every atom in every timestep. Shape `n_timesteps` x `n_atoms` x `n_features`)
            If the trajectory instance is indexed by str, the array has shape `n_timesteps` x `n_features`.
            If the trajectory instance is indexed by str, the array has shape `n_atoms` x `n_features`.
            If the trajectory instance is indexed by slice, the array has shape `slice`, `n_atoms` x `n_features`.
        """
        
        from ichor.files import PointsDirectory, Trajectory
        if isinstance(self, Trajectory):
            features = np.array([timestep.alf_features(alf) for timestep in self])
        elif isinstance(self, PointsDirectory):
            features = np.array([point.alf_features(alf) for point in self])
            
        if features.ndim == 3:
            features = np.transpose(features, (1, 0, 2))
        return features

    def coordinates_to_xyz(
        self, fname: Optional[Union[str, Path]] = None, step: Optional[int] = 1
    ):
        """write a new .xyz file that contains the timestep i, as well as the coordinates of the atoms
        for that timestep.

        :param fname: The file name to which to write the timesteps/coordinates
        :param step: Write coordinates for every n^th step. Default is 1, so writes coordinates for every step
        """
        from ichor.files.point_directory import PointDirectory

        if fname is None:
            fname = Path("system_to_xyz.xyz")
        elif isinstance(fname, str):
            fname = Path(fname)

        fname = fname.with_suffix(".xyz")

        with open(fname, "w") as f:
            for i, point in enumerate(self[::step]):
                # this is used when self is a PointsDirectory, so you are iterating over PointDirectory instances
                if isinstance(point, PointDirectory):
                    f.write(f"    {len(point.atoms)}\ni = {i}\n")
                    for atom in point.atoms:
                        f.write(
                            f"{atom.type} {atom.x:16.8f} {atom.y:16.8f} {atom.z:16.8f}\n"
                        )
                # this is used when self is a Trajectory and you are iterating over Atoms instances
                else:
                    f.write(f"    {len(point)}\ni = {i}\n")
                    for atom in point:
                        f.write(
                            f"{atom.type} {atom.x:16.8f} {atom.y:16.8f} {atom.z:16.8f}\n"
                        )

    def features_to_csv(
        self,
        fname: Optional[Union[str, Path]] = None,
        atom_names: Optional[List[str]] = None,
    ):
        """Writes csv files containing features for every atom in the system. Optionally a list can be passed in to get csv files for only a subset of atoms

        :param fname: A string to be appended to the default csv file names. A .csv file is written out for every atom with default name `atom_name`_features.csv
            If an fname is given, the name becomes `fname`_`atom_name`_features.csv
        :param atom_names: A list of atom names for which to write csv files
        """
        import pandas as pd

        if isinstance(atom_names, str):
            atom_names = [atom_names]

        # whether to write csvs for all atoms or subset
        if atom_names is None:
            atom_names = self.atom_names

        for atom_name in atom_names:
            atom_features = self[atom_name].features
            df = pd.DataFrame(atom_features, columns=self.get_headings())
            if fname is None:
                df.to_csv(f"{atom_name}_features.csv")
            else:
                df.to_csv(f"{fname}_{atom_name}_features.csv")

    def features_to_excel(
        self,
        fname: Optional[Union[str, Path]] = None,
        atom_names: List[str] = None,
    ):
        """Writes out one excel file which contains a sheet with features for every atom in the system. Optionally a list of atom names can be
        passed in to only make sheets for certain atoms

        :param atom_names: A list of atom names for which to calculate features and write in excel spreadsheet
        """
        import pandas as pd

        if fname is None:
            fname = Path("features_to_excel.xlsx")
        elif isinstance(fname, str):
            fname = Path(fname)

        fname = fname.with_suffix(".xlsx")

        if isinstance(atom_names, str):
            atom_names = [atom_names]
        # whether to write excel sheets for all atoms or subset
        if atom_names is None:
            atom_names = self.atom_names

        dataframes = {}

        for atom_name in atom_names:
            atom_features = self[atom_name].features
            df = pd.DataFrame(atom_features, columns=self.get_headings())
            dataframes[atom_name] = df

        with pd.ExcelWriter(fname) as workbook:
            for atom_name, df in dataframes.items():
                df.columns = self.get_headings()
                df.to_excel(workbook, sheet_name=atom_name)

    def get_headings(self):
        headings = ["bond1", "bond2", "angle"]

        remaining_features = (
            len(self[0].features[-1]) - 3
        )  # Removes bond1, bond 2, angle
        remaining_features = int(
            remaining_features / 3
        )  # each feature has r, theta, phi component

        for feat in range(remaining_features):
            headings.append(f"r{feat+3}")  # starts at r3
            headings.append(f"theta{feat+3}")  # starts at theta3
            headings.append(f"phi{feat+3}")  # starts at phi3

        return headings

    def iteratoms(self):
        """Returns a generator of AtomView instances for each atom stored in ListOfAtoms."""
        for atom in self.atom_names:
            yield self[atom]

    def __getitem__(self, item: Union[int, str]):
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
                :param atom: A string reperesenting the name of an atom, e.g. 'C1', 'H2', etc.
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
                    """Returuns the name of the atom, e.g. 'C1', 'H2', etc."""
                    return self._atom

                @property
                def atom_names(self):
                    """Returns a list of atom names, since the AtomView only stores information for one atom, this list has one element."""
                    return [self._atom]

                @property
                def types(self):
                    """Returns the types of atoms in the atom view. Since only one atom type is present, it returns a list with one element"""
                    return [self[0].type]

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
                    # set this attribute because the next line is going to slice the parent instance, which will then call this part of ListOfAtoms.__getitem__() again
                    # which will cause an infinite recursion
                    setattr(parent, "get_slice", True)
                    # extend the AtomSlice (which is an empty list) with the slice from parent
                    self.extend(parent[sl])
                    # remove the get_slice attribute again, so that an AtomSlice can be indexed again
                    delattr(parent, "get_slice")

            if hasattr(self, "get_slice"):
                return super().__getitem__(item)
            return AtomSlice(self, item)

        # if indexing by something else that has not been programmed yet, should only be reached if not indexed by int, str, or slice
        raise TypeError(
            f"Cannot index type '{self.__class__.__name__}' with type '{type(item)}"
        )
