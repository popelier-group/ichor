import json
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from ichor.core.atoms import ALF, Atoms, ListOfAtoms
from ichor.core.calculators.alf import default_alf_calculator
from ichor.core.calculators.features.alf_features_calculator import (
    calculate_alf_features,
)
from ichor.core.common import constants
from ichor.core.common.io import mkdir
from ichor.core.common.itertools import chunker
from ichor.core.database.json import get_data_for_point
from ichor.core.database.sql import (
    add_atom_names_to_database,
    add_point_to_database,
    create_database,
    create_database_session,
)
from ichor.core.files import GJF
from ichor.core.files.directory import Directory
from ichor.core.files.point_directory import PointDirectory
from ichor.core.files.xyz import Trajectory, XYZ


class PointsDirectory(ListOfAtoms, Directory):
    """
    A helper class that wraps around a directory which contains points (molecules with various geometries).
    Calling Directory.__init__(self, path) will call the `parse` method of PointsDirectory instead of Directory
    (because Python looks for the method in this class first before looking at parent class methods.) A typical ICHOR
    directory that contains points will points will have a structure like this:

    .. code-block:: text

        -TRAINING_SET
            -- SYSTEM_NAME000
            -- SYSTEM_NAME001
            -- SYSTEM_NAME002
            ........

    Each of the subdirectories contains Gaussian files (such as .gjf),
    as well as an `atomic_files` directory, which then contains the AIMALL files.
    A `PointsDirectory` will wrap around the whole TRAINING_SET directory
    (which contains multiple points), while a `PointDirectory` will wrap around a SYSTEM_NAME00...
    folder (which only contains information about 1 point).

    :param path: Path to a directory which contains points.
        This path is typically the path to the training set, sample pool, etc.
    :param needs_parsing: By default, every PointsDirectory is parsed when the instance is created to
        create PointDirectory instances of each inner directory (but the contents of the files are not read).
        If however, a slice of a already created PointsDirectory is made, the contents of the directories
        do not need to be parsed again, so needs_parsing would be false
    """

    _suffix = ".pointsdir"

    def __init__(self, path: Union[Path, str], needs_parsing=True, *args, **kwargs):
        # Initialise `list` parent class of `ListOfAtoms`
        ListOfAtoms.__init__(self, *args, **kwargs)
        if needs_parsing:
            # this will call Directory __init__ method (which then calls self.parse)
            # since PointsDirectory implements a `parse` method, it will be called instead of the Directory parse method

            Directory.__init__(self, path)

    @classmethod
    def check_path(cls, path: Path) -> bool:
        """Makes sure that path is PointsDirectory-like"""
        return (path.suffix == cls._suffix) and path.is_dir()

    def _parse(self) -> None:
        """
        Called from Directory.__init__(self, path)
        Parse a directory (such as TRAINING_SET, TEST_SET,etc.)
        and make PointDirectory objects of each of the subirectories.
        If however there are only .gjf files present in the directory at the moment,
        then make a new directory for each .gjf file and move the .gjf file in there. So for example,
        if there is a file called WATER001.gjf, this method will make a folder called WATER001
        and will move WATER001.gjf in it.
        Initially when the training set, test set, and sample pool directories are made,
        there are only .gjf files present in the
        directory. This method makes them in separate directories.
        """

        # iterdir sorts by name, see Directory class
        for f in self.iterdir():
            # if the current PathObject is a directory that matches
            # a PointDirectory instance and add to self
            if PointDirectory.check_path(f):
                point = PointDirectory(f)
                self.append(point)
            elif f.is_file() and f.suffix in {XYZ.get_filetype(), GJF.get_filetype()}:
                new_dir = self.path / (f.stem + PointDirectory._suffix)
                mkdir(new_dir)
                # move the file into the newly made directory
                f.replace(new_dir / f.name)
                self.append(PointDirectory(new_dir))

        # wrap the new directory as a PointDirectory instance and add to self
        # sort by the names of the directories (by the numbers in their name)
        # since the system name is always the same
        self = self.sort(key=lambda x: x.path.name)

    # TODO: move to processing function
    @property
    def wfn_energy(self) -> np.ndarray:
        """Returns np array of wfn energies of all points

        :return: np array of total energy (in Hartree) for all points
        """
        return np.array([point.wfn.total_energy for point in self])

    # TODO: move to processing function
    @property
    def total_energy(self):
        """
        Returns np array of wfn energies of all points

        :return: np array of total energy (in Hartree) for all points
        """
        return self.wfn_energy

    # TODO: move to processing function
    def connectivity(
        self, connectivity_calculator: Callable[..., np.ndarray]
    ) -> np.ndarray:
        """
        Return the connectivity matrix (n_atoms x n_atoms) for the given Atoms instance.

        Returns:
            :type: `np.ndarray` of shape n_atoms x n_atoms
        """

        return connectivity_calculator(self[0].atoms)

    # TODO: move to processing function
    def alf(self, alf_calculator: Callable[..., ALF], *args, **kwargs) -> List[ALF]:
        """
        Returns the Atomic Local Frame (ALF) for all Atom instances that are held in Atoms
        e.g. ``[[0,1,2],[1,0,2], [2,0,1]]``.

        :param \*args: positional arguments to pass to alf calculator
        :param \**kwargs: key word arguments to pass to alf calculator
        """
        return [
            alf_calculator(atom_instance, *args, **kwargs)
            for atom_instance in self[0].atoms
        ]

    # TODO: move to processing function
    def alf_dict(
        self, alf_calculator: Callable[..., ALF], *args, **kwargs
    ) -> Dict[str, ALF]:
        """
        Returns a dictionary of key: atom_name, value: ALF instance
            (containing central atom index, x-axis idx, xy-plane idx)

        e.g. ``{"O1":ALF(0,1,2),"H2":ALF(1,0,2), "H3":ALF(2,0,1)]``.

        :param \*args: positional arguments to pass to alf calculator
        :param \**kwargs: key word arguments to pass to alf calculator
        """
        return self[0].alf_dict(alf_calculator, *args)

    # TODO: move to processing function
    def properties(
        self, system_alf: Optional[List[ALF]] = None, specific_property: str = None
    ):
        """Get properties contained in the PointDirectory.
        IF no system alf is passed in, an automatic process to get C matrices is started.

        :param system_alf: Optional list of `ALF` instances that can be passed in
            to use a specific alf instead of automatically trying to compute it.
        :param key: return only a specific key from the returned dictionary
        """

        if not system_alf:
            # TODO: The default alf calculator (the cahn ingold prelog one)
            # should accept connectivity, not connectivity calculator, so connectivity also needs to be passed in.
            system_alf = self.alf(default_alf_calculator)

        points_dir_properties = {}

        for point in self:
            points_dir_properties[point.name] = point.properties(system_alf)

        if specific_property:
            return points_dir_properties[specific_property]

        return points_dir_properties

    @property
    def types(self) -> List[str]:
        """Returns the atom elements for atoms, assumes each timesteps has the same atoms.
        Removes duplicates."""
        return self[0].atoms.types

    @property
    def types_extended(self) -> List[str]:
        """Returns the atom elements for atoms, assumes each timesteps has the same atoms.
        Removes duplicates."""
        return self[0].atoms.types_extended

    @property
    def atom_names(self) -> List[str]:
        """Return the atom names from the first timestep. Assumes that all timesteps have the same
        number of atoms/atom names."""
        return self[0].atoms.atom_names

    @property
    def natoms(self) -> int:
        """Returns the number of atoms in the first timestep. Each timestep should have the same number of atoms."""
        return len(self[0].atoms)

    @property
    def coordinates(self) -> np.ndarray:
        """
        :return: the xyz coordinates of all atoms for all timesteps. Shape `n_timesteps` x `n_atoms` x `3`
        """
        return np.array([timestep.atoms.coordinates for timestep in self])

    def coordinates_to_xyz(
        self,
        fname: Optional[Union[str, Path]] = Path("system_to_xyz.xyz"),
        step: Optional[int] = 1,
    ):
        """write a new .xyz file that contains the timestep i, as well as the coordinates of the atoms
        for that timestep.

        :param fname: The file name to which to write the timesteps/coordinates
        :param step: Write coordinates for every n^th step. Default is 1, so writes coordinates for every step
        """

        fname = Path(fname)
        fname = fname.with_suffix(".xyz")

        with open(fname, "w") as f:
            for i, point in enumerate(self[::step]):
                # this is used when self is a PointsDirectory, so you are iterating over PointDirectory instances
                f.write(f"    {len(point.atoms)}\ni = {i}\n")
                for atom in point.atoms:
                    f.write(
                        f"{atom.type} {atom.x:16.8f} {atom.y:16.8f} {atom.z:16.8f}\n"
                    )

    def coordinates_to_xyz_with_errors(
        self,
        models_path: Union[str, Path],
        fname: Optional[Union[str, Path]] = Path("xyz_with_properties_error.xyz"),
        step: Optional[int] = 1,
    ):
        """
        Write a new .xyz file that contains the timestep i, as well as the coordinates of the atoms
        for that timestep. The comment lines in the xyz have absolute predictions errors.
        These can then be plotted in ALFVisualizer as cmap to see where poor predictions happen.

        :param models_path: The model path to one atom.
        :param property_: The property for which to predict for and get errors (iqa or any multipole moment)
        :param fname: The file name to which to write the timesteps/coordinates
        :param step: Write coordinates for every n^th step. Default is 1, so writes coordinates for every step
        """

        from ichor.core.analysis.predictions import get_true_predicted
        from ichor.core.common.constants import ha_to_kj_mol
        from ichor.core.models import Models

        models_path = Path(models_path)

        models = Models(models_path)
        true, predicted = get_true_predicted(models, self)
        # transpose to get keys to be the properties (iqa, q00, etc.) instead of them being the values
        true = true.T
        predicted = predicted.T
        # error is still a ModelResult
        error = (true - predicted).abs()
        # if iqa is in dictionary, convert that to kj mol-1
        if error.get("iqa"):
            error["iqa"] *= ha_to_kj_mol
        # dispersion is added onto iqa, so also calculate in kj mol-1
        if error.get("dispersion"):
            error["dispersion"] *= ha_to_kj_mol

        # order the properties: iqa, q00, q10,....
        error = dict(sorted(error.items()))

        fname = fname.with_suffix(".xyz")

        with open(fname, "w") as f:
            for i, point in enumerate(self[::step]):
                # this is used when self is a PointsDirectory, so you are iterating over PointDirectory instances

                # {atom_name : {prop1: val, prop2: val}, atom_name2: {prop1: val, prop2: val}, ....} for one timestep
                dict_to_write = {
                    outer_k: {
                        inner_k: inner_v[i] for inner_k, inner_v in outer_v.items()
                    }
                    for outer_k, outer_v in error.items()
                }
                f.write(
                    f"    {len(point.atoms)}\ni = {i} properties_error = {dict_to_write}\n"
                )
                for atom in point.atoms:
                    f.write(
                        f"{atom.type} {atom.x:16.8f} {atom.y:16.8f} {atom.z:16.8f}\n"
                    )

    @classmethod
    def from_trajectory(
        cls,
        trajectory_path: Union[str, Path],
        system_name: str = None,
        every=1,
        center=True,
    ) -> "PointsDirectory":
        """
        Generate a PointsDirectory-type structure directory from a trajectory (.xyz) file

        :param trajectory_path: A str or Path to a .xyz file containing geometries
        :param system_name: The name of the chemical system. This is going to be the name of the directory
            which will be created.
        :param center: Whether to center the geometries on the centroid of the system. This is useful to prevent
            the molecule from translating in 3D space (and prevents issues with WFN files, where a very large x,y,z
            value (over 100) for the coordinates leads to ******** being written in the .wfn file...)
        """

        traj = Trajectory(trajectory_path)

        if not system_name:
            system_name = traj.path.stem

        dir_path = traj.to_dir(system_name, every=every, center=center)
        return PointsDirectory(dir_path)

    def __getitem__(self, item: Union[int, str]) -> Union[Atoms, ListOfAtoms]:
        """Used when indexing a Trajectory instance by an integer, string, or slice."""

        # if ListOfAtoms instance is indexed by an integer or np.int64, then index as a list
        if isinstance(item, (int, np.int64)):
            return list.__getitem__(self, item)

        # if ListOfAtoms is indexed by a string, such as an atom name (eg. C1, H2, O3, H4, etc.)
        elif isinstance(item, str):
            from ichor.core.atoms.list_of_atoms_atom_view import AtomView

            return AtomView(self, item)

        # if PointsDirectory is indexed by a slice e.g. [:50], [20:40], etc.
        elif isinstance(item, slice):

            return PointsDirectory(self.path, False, list.__getitem__(self, item))

        # if PointsDirectory is indexed by a list, e.g. [0, 5, 10]
        elif isinstance(item, (list, np.ndarray)):

            return PointsDirectory(
                self.path, False, [list.__getitem__(self, i) for i in item]
            )

        # if indexing by something else that has not been programmed yet, should only
        # be reached if not indexed by int, str, or slice
        raise TypeError(
            f"Cannot index type '{self.__class__.__name__}' with type '{type(item)}"
        )

    def write_to_sqlite3_database(
        self, db_path: Union[str, Path] = None, echo=False, print_missing_data=True
    ) -> Path:
        """
        Write out important information from a PointsDirectory instance to an SQLite3 database.

        :param db_path: database to write to
        :param echo: Whether to print out SQL queries from SQL Alchemy
        :param echo: Whether to print out SQL queries from SQL Alchemy, defaults to False
        :param print_missing_data: Whether to print out any missing data from each PointDirectory contained
            in self, defaults to False
        :return: The path to the written SQL database
        """

        if not db_path:
            db_path = Path(f"{self.name_without_suffix}.sqlite")
        else:
            db_path = Path(db_path).with_suffix(".sqlite")

        # if db exists, then add new points to existing database.
        if db_path.exists():
            print("Database already exists. Adding new points to database...")
            session = create_database_session(db_path)
            for point in self:
                add_point_to_database(
                    session, point, echo=echo, print_missing_data=print_missing_data
                )
        else:
            print("Making new database and adding points...")
            create_database(db_path, echo)
            session = create_database_session(db_path)
            add_atom_names_to_database(session, self.atom_names, echo=echo)
            for point in self:
                add_point_to_database(
                    session, point, echo=echo, print_missing_data=print_missing_data
                )

        return db_path

    def write_to_json_database(
        self,
        root_path: Union[str, Path] = None,
        datafunction: Callable = get_data_for_point,
        npoints_per_json=500,
        print_missing_data=True,
        indent: int = 2,
        separators=(",", ":"),
    ) -> Path:
        """
        Write out important information from a PointsDirectory instance to a json file.

        :param root_path: Name of directory which will the json database. This is a directory,
            which contains multiple directories inside. Each directory inside is one PointsDirectory.
            The reason for implementing like this is if using for multiple PointsDirectory-ies
            at once, so that data for each PointDirectory is written in a separate folder
        :param datafunction: A function used to get all data for a single point.
            This data is going to get written to the json file.
        :param npoints_per_json: Maximum number of geometries to write to one json file
            This is done so that the individual files do not become very large.
        :param print_missing_data: Whether to print out any missing data from each PointDirectory contained
            in self, defaults to False
        :param indent: integer representing number of spaces to indent, defaults to 2
        :param separators: Separators used for each entry, default (",", ":")
        :return: The path to the written json file
        """

        root_path = Path(root_path)

        # if no path is given use pointdirectory without suffix
        if not root_path:
            root_path = Path(self.name_without_suffix)

        # add a _json to the directory
        root_path = root_path.with_name(root_path.name + "_json")

        mkdir(root_path)

        # json file name that will be modified
        tmp_json_file_name = root_path.stem

        counter = 0
        json_file_path = root_path / f"{tmp_json_file_name}_{counter}.json"

        total_data_list = []

        for chunk in chunker(self, npoints_per_json):

            for point in chunk:

                total_data_list.append(
                    datafunction(point, print_missing_data=print_missing_data)
                )

            with open(json_file_path, "w") as json_db:
                json.dump(
                    total_data_list, json_db, indent=indent, separators=separators
                )

                total_data_list = []
                counter += 1
                json_file_path = root_path / f"{tmp_json_file_name}_{counter}.json"

        return root_path

    # TODO: move processing code to processing func
    def features_with_properties_to_csv(
        self,
        system_alf: Dict[str, ALF],
        str_to_append_to_fname: str = "_features_with_properties.csv",
        atom_names: Optional[List[str]] = None,
        property_types: Optional[List[str]] = None,
        **kwargs,
    ):
        """
        Calculates ALF features and properties (with multipole moments rotated).

        :param str_to_append_to_fname: a string that is appended to the default file name
            (which is ``name_of_atom.csv``), defaults to None
        :param atom_names: A list of atom names for which to write out csv files with properties.
            If None, then writes out files for all atoms in the system, defaults to None
        :param property_types: A list of property names (iqa, multipole names) for which to write columns.
            If None, then writes out columns for all properties, defaults to None
        :param \*args: positional arguments to pass to calculator function
        :param \**kwargs: key word arguments to be passed to the feature calculator function
        :raises TypeError: This method only works for PointsDirectory instances because it
            needs access to AIMALL information. Does not work for Trajectory instances.
        """

        if not atom_names:
            atom_names = self.atom_names
        elif isinstance(atom_names, str):
            atom_names = [atom_names]

        # TODO: add dispersion later if we are going to make models for it separately
        if not property_types:
            property_types = ["iqa", "integration_error"] + constants.multipole_names

        for atom_name in atom_names:

            training_data = []
            features = self[atom_name].features(
                calculate_alf_features, system_alf, **kwargs
            )

            for i, point in enumerate(self):
                point_properties_dict = point.properties(system_alf)
                properties = [
                    point_properties_dict.get(atom_name).get(ty)
                    for ty in property_types
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

    # TODO: move processing code to processing function
    def features_with_wfn_energy_and_dE_df_to_csv(
        self,
        alf_list: List[ALF],
        central_atom_idx: int,
        str_to_append_to_fname: str = "_features_with_dE_df.csv",
        **kwargs,
    ):
        """Writes out a csv file containing wfn energy and FORCEs calculated for every feature.
        Note that the forces (dE/df_i) are the negative of the PES gradient,
        so for machine learning, the negative of these forces needs to be taken to
        add gradient information into GP models.

        :param system_alf: A list of ALF instances containing alf info
        :param central_atom_idx: The central atom which to center the alf on
            and for which dE/df will be calculated
        :type central_atom_idx: int
        :param str_to_append_to_fname: _description_, defaults to "_features_with_properties.csv"
        :type str_to_append_to_fname: str, optional
        """

        from ichor.core.models.gaussian_energy_derivative_wrt_features import (
            convert_to_feature_forces,
            form_b_matrix,
        )

        training_data = []
        for point_dir in self:

            atoms = point_dir.xyz.atoms
            features = atoms[central_atom_idx].features(
                calculate_alf_features, alf_list
            )
            nfeatures = len(features)
            wfn_energy = point_dir.wfn.total_energy
            b_matrix = form_b_matrix(atoms, alf_list, central_atom_idx)
            cart_forces = np.array(
                list(point_dir.gaussian_output.global_forces.values())
            )
            dE_df = convert_to_feature_forces(
                cart_forces, b_matrix, alf_list, central_atom_idx
            )
            training_data.append([*features, wfn_energy, *dE_df])

            input_headers = [f"f{i+1}" for i in range(nfeatures)]
            output_headers = ["wfn_energy"] + [f"-dEdf{i+1}" for i in range(nfeatures)]

            fname = atoms[central_atom_idx].name + str_to_append_to_fname

        df = pd.DataFrame(
            training_data,
            columns=input_headers + output_headers,
            dtype=np.float64,
        )
        df.to_csv(fname, index=False)
