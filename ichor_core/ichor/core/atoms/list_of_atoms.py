from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

import numpy as np
from ichor.core.atoms.atoms import ALF, Atoms
from ichor.core.calculators import calculate_alf_features


class ListOfAtoms(list, ABC):
    """
    Used to focus only on how one atom moves in a trajectory, so the user can do something
    like trajectory['C1'] where trajectory is an instance of class Trajectory. This way the
    user can also do trajectory['C1'].features, trajectory['C1'].coordinates, etc.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @abstractmethod
    def connectivity(self) -> np.ndarray:
        """Returns the connectivity matrix of the first timestep."""
        ...

    @abstractmethod
    def alf(self) -> "ALF":
        """Returns the atomic local frame for the first timestep."""
        ...

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
        """Abstract method for natoms.

        :return: Returns the number of atoms in the first timestep. Each timestep should have the same number of atoms.
        """
        ...

    @property
    @abstractmethod
    def coordinates(self) -> np.ndarray:
        """Abstract method for coordinates.

        :return: the xyz coordinates of all atoms for all timesteps. Shape `n_timesteps` x `n_atoms` x `3`
        """
        ...

    def features(
        self,
        feature_calculator: Callable[..., np.ndarray],
        *args,
        is_atomic=True,
        **kwargs,
    ) -> np.ndarray:
        """
        Return the ndarray of features. This is assumed to be either 2D or 3D array.
        If the dimensionality of the feature array is 3, the array is transposed to transform a
        (ntimestep, natom, nfeature) array into a (natom, ntimestep, nfeature) array so that
        all features for a single atom are easier to group.

        :param feature_calculator: The calculator function which calculates features
        :param is_atomic: Whether the calculator calculates features for individual atoms
            or the whole geometry
        :param args: Positional arguments to pass to feature calculator function
        :param kwargs: Key word arguments to pass to feature calculator function
        :return: If the features for the whole trajectory are returned,
            the array has shape `n_atoms` x `n_timesteps` x `n_features`
            If the trajectory instance is indexed by str, the array has shape `n_timesteps` x `n_features`.
            If the trajectory instance is indexed by int, the array has shape `n_atoms` x `n_features`.
            If the trajectory instance is indexed by slice, the array has shape `n_atoms` x`slice` x `n_features`.
            If a non-atomic calculator is passed, a `n_timesteps` x features (features could be vector, matrix, etc)
            is returned.
        """
        return np.array(
            [
                timestep.features(
                    feature_calculator, *args, is_atomic=is_atomic, **kwargs
                )
                for timestep in self
            ]
        )

    def get_headings(self):
        """
        Helper function which makes the column headings
        for csv or excel files in which features are going to be saved.
        """

        natoms = self.natoms
        nfeatures = 3 * natoms - 6 if natoms > 1 else 1

        if nfeatures == 1:
            return ["bond1"]

        headings = ["bond1", "bond2", "angle"]

        remaining_features = nfeatures - 3
        remaining_features = int(
            remaining_features / 3
        )  # each feature has r, theta, phi component

        for feat in range(remaining_features):
            headings += [f"r{feat + 3}", f"theta{feat + 3}", f"phi{feat + 3}"]

        return headings

    def features_to_csv(
        self,
        feature_calculator: Callable[..., np.ndarray],
        *args,
        fname: Optional[Union[str, Path]] = None,
        atom_names: Optional[List[str]] = None,
        **kwargs,
    ):
        """
        Writes csv files containing features for every atom in the system.
        Optionally a list can be passed in to get csv files for only a subset of atoms.

        :param feature_calculator: Calculator function to be used to calculate features
        :param fname: A string to be appended to the default csv file names.
            A .csv file is written out for every atom with default name ``atom_name_features.csv``
            If an fname is given, the name becomes ``fname_atom_name_features.csv``
        :param atom_names: A list of atom names for which to write csv files.
            If None, then write out the features for every atom in the system.
        :param args: positional arguments to pass to calculator function
        :param kwargs: key word arguments to be passed to the feature calculator function
        """
        import pandas as pd

        # whether to write csvs for all atoms or subset
        if atom_names is None:
            atom_names = self.atom_names
        elif isinstance(atom_names, str):
            atom_names = [atom_names]

        for atom_name in atom_names:
            atom_features = self[atom_name].features(
                feature_calculator, *args, **kwargs
            )
            df = pd.DataFrame(atom_features, columns=self.get_headings())
            if fname is None:
                df.to_csv(f"{atom_name}_features.csv", index=None)
            else:
                df.to_csv(f"{fname}_{atom_name}_features.csv", index=None)

    def features_to_excel(
        self,
        feature_calculator: Union["ALF", Callable],
        *args,
        fname: Union[str, Path] = Path("features_to_excel.xlsx"),
        atom_names: List[str] = None,
        **kwargs,
    ):
        """Writes out one excel file which contains a sheet with
        features for every atom in the system. Optionally a list of atom names can be
        passed in to only make sheets for certain atoms

        :param atom_names: A list of atom names for which to calculate features and write in excel spreadsheet
        :param args: positional arguments to pass to calculator function
        :param kwargs: key word arguments to be passed to the feature calculator function
        :param fname: File name to save features to
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
            atom_features = self[atom_name].features(
                feature_calculator, *args, **kwargs
            )
            df = pd.DataFrame(atom_features, columns=self.get_headings())
            dataframes[atom_name] = df

        with pd.ExcelWriter(fname) as workbook:
            for atom_name, df in dataframes.items():
                df.columns = self.get_headings()
                df.to_excel(workbook, sheet_name=atom_name)

    def center_geometries_on_atom_and_write_xyz(
        self,
        central_atom_name: str,
        system_alf: Dict[str, ALF],
        fname: Optional[Union[str, Path]] = None,
    ):
        """Centers all geometries (from a Trajectory of PointsDirectory instance)
        onto a central atom and then writes out a new xyz file with all geometries centered on that atom.
        This is essentially what the ALFVisualizier application (ALFi) does.
        The features for the central atom are calculated, after which they
        are converted back into xyz coordinates.
        Thus all geometries are now centered on the given central atom).

        :param feature_calculator: Function which calculates features
        :param central_atom_name: the name of the central atom to center
            all geometries on. Eg. 'O1'
        :param fname: Optional file name in which to save the rotated geometries.
        :param args: Positional arguments to pass to calculator function
        :param kwargs: Key word arguments to pass to calculator function
        """

        from ichor.core.atoms import Atom
        from ichor.core.calculators import alf_features_to_coordinates
        from ichor.core.common.units import AtomicDistance
        from ichor.core.files import Trajectory

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
        central_atom_alf = system_alf[central_atom_name]
        # before, ordering is 0,1,2,3,4,5,...,etc.
        # after calculating the features and converting back, the order is going to be
        # central atom idx, x-axis atom index, xy-plane atom index, rest of atom indices
        n_atoms = self.natoms
        previous_atom_ordering = list(range(n_atoms))
        current_atom_ordering = list(central_atom_alf) + [
            i for i in range(n_atoms) if i not in central_atom_alf
        ]
        # this will get the index that the atom was moved to after reordering.
        reverse_alf_ordering = [
            current_atom_ordering.index(num) for num in range(n_atoms)
        ]
        # order will always be central atom(0,0,0), x-axis atom, xy-plane atom, etc.
        xyz_array = alf_features_to_coordinates(
            self[central_atom_name].features(calculate_alf_features, system_alf)
        )
        # reverse the ordering, so that the rows are the same as before
        # can now use the atom names sequence as they were read in
        # in initial Trajectory/PointsDirectory instance.
        xyz_array[:, previous_atom_ordering, :] = xyz_array[:, reverse_alf_ordering, :]
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
