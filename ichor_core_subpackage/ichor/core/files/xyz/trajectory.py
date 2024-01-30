import re
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Union

import numpy as np
import pandas as pd
from ichor.core.atoms import Atom, Atoms, ListOfAtoms
from ichor.core.atoms.alf import ALF
from ichor.core.calculators import alf_features_to_coordinates
from ichor.core.common.constants import bohr2ang
from ichor.core.common.int import count_digits
from ichor.core.common.io import convert_to_path, mkdir
from ichor.core.common.itertools import chunker
from ichor.core.files.file import FileState, ReadFile, WriteFile


class Trajectory(ReadFile, WriteFile, ListOfAtoms):
    """
    Handles .xyz files that have multiple timesteps, with each timestep giving the x y z coordinates of the
    atoms. A user can also initialize an empty trajectory and append ``Atoms``
    instances to it without reading in a .xyz file. This allows
    the user to build custom trajectories containing any sort of geometries.

    :param path: The path to a .xyz file that contains timesteps.
        Set to None by default as the user can initialize an empty trajectory and built it up
        themselves
    """

    filetype = ".xyz"

    def __init__(self, path: Union[Path, str], *args, **kwargs):
        ListOfAtoms.__init__(self, *args, **kwargs)
        super(ReadFile, self).__init__(path)

    def _read_file(self):

        with open(self.path, "r") as f:
            # make empty Atoms instance in which to store one timestep
            atoms = Atoms()
            for line in f:
                # match the line containing the number of atoms in timestep
                if re.match(r"^\s*\d+", line):
                    natoms = int(line)
                    # this is the comment line of xyz files.
                    # It can be empty or contain some useful information that can be stored.
                    line = next(f)
                    # if the comment line properties errors, we can store these

                    # TODO: do we still need to get properties in trajectory? - if we do, implement without ast
                    # if re.match(r"^\s*?i\s*?=\s*?\d+\s*properties_error", line):
                    #     properties_error = line.split("=")[-1].strip()
                    #     atoms.properties_error = ast.literal_eval(properties_error)

                    # the next line after the comment line is where coordinates begin
                    for _ in range(natoms):
                        line = next(f)
                        # add *_ to work for extended xyz which contain extra information after x,y,z coordinates
                        atom_type, x, y, z, *_ = line.split()
                        atoms.add(Atom(atom_type, float(x), float(y), float(z)))

                    # add the Atoms instance to the Trajectory instance
                    self.add(atoms)
                    # make new Atoms instance where next timestep can be stored
                    atoms = Atoms()

    @property
    def types(self):
        """Returns the atom elements for atoms, assumes each timesteps has the same atoms.
        Removes duplicates."""
        return self[0].types

    @property
    def types_extended(self):
        """Returns the atom elements for atoms, assumes each timesteps has the same atoms.
        Removes duplicates."""
        return self[0].types_extended

    @property
    def atom_names(self):
        """Return the atom names from the first timestep. Assumes that all timesteps have the same
        number of atoms/atom names."""
        return self[0].atom_names

    @property
    def natoms(self):
        """Returns the number of atoms in the first timestep. Each timestep should have the same number of atoms."""
        return len(self[0])

    @property
    def coordinates(self) -> np.ndarray:
        """
        Returns:
            :type: `np.ndarray`
            the xyz coordinates of all atoms for all timesteps. Shape `n_timesteps` x `n_atoms` x `3`
        """

        return np.array([timestep.coordinates for timestep in self])

    def connectivity(
        self, connectivity_calculator: Callable[..., np.ndarray]
    ) -> np.ndarray:
        """
        Return the connectivity matrix ``n_atoms x n_atoms`` for the given Atoms instance.

        :rtype: `np.ndarray` of shape n_atoms x n_atoms
        """
        return connectivity_calculator(self[0])

    def alf(self, alf_calculator: Callable[..., ALF], *args, **kwargs) -> List[ALF]:
        """
        Returns the Atomic Local Frame (ALF) for all Atom instances that are held in Atoms.
        e.g. ``[[0,1,2],[1,0,2], [2,0,1]]``

        :param \*args: positional arguments to pass to alf calculator
        :param \**kwargs: key word arguments to pass to alf calculator
        """
        return [
            alf_calculator(atom_instance, *args, **kwargs) for atom_instance in self[0]
        ]

    def alf_dict(
        self, alf_calculator: Callable[..., ALF], *args, **kwargs
    ) -> Dict[str, ALF]:
        """Returns a dictionary with the atomic local frame indices for every atom (0-indexed)."""
        return {
            atom_instance.name: atom_instance.alf(alf_calculator, *args, **kwargs)
            for atom_instance in self[0]
        }

    def add(self, atoms):
        """Add a list of Atoms (corresponding to one timestep) to the end of the trajectory list"""
        if isinstance(atoms, Atoms):
            self.append(atoms)
        else:
            raise ValueError(f"Cannot add an instance of {type(atoms)} to self.")

    def rmsd(self, ref=None):
        if ref is None:
            ref = self[0]
        elif isinstance(ref, int):
            ref = self[ref]

        return [ref.rmsd(point) for point in self]

    def to_dir(self, system_name: str, every: int = 1, center=False):
        """Writes out every nth timestep to a separate .xyz file to a given directory

        :param system_name: The name of the system. This will be the name of the
            given directory, with a suffix added. Default suffix is PointsDirectory._suffix
        :param every: An integer value that indicates the nth step at which an
            xyz file should be written. Default is 1. If
            a value eg. 5 is given, then it will only write out a .xyz file for every 5th timestep.
        """
        from ichor.core.files import PointsDirectory, XYZ

        default_root_suffix = PointsDirectory._suffix

        # capitalize system name
        system_name = system_name.upper()
        root_path = Path(system_name).with_suffix(default_root_suffix)

        mkdir(root_path, empty=True)
        for i, atoms_instance in enumerate(self):

            if (i % every) == 0:
                if center:
                    atoms_instance.centre()
                point_name = (
                    f"{system_name}{str(i).zfill(max(4, count_digits(len(self))))}.xyz"
                )
                path = Path(point_name)
                path = root_path / path
                xyz_file = XYZ(path, atoms_instance)
                xyz_file.write()

    def to_dirs(
        self,
        system_name: str,
        split_size: int = 1000,
        every: int = 1,
        center=False,
    ):
        """Writes out every nth timestep to a separate .xyz file. This method differs
        from `to_dir` because it has a structure system_name_root / points_directory / xyz file.
        I.e. there is an additional root directory which encapsulates all the PointsDirectory-like
        directories.

        :param system_name: The name of the system. This will be used in the names of the files
            and directories as well
        :param split_size: How many .xyz files are going to be in each of the inner
            PointsDirectory-like directories
        :param every: An integer value that indicates the nth step at
            which an xyz file should be written. Default is 1.
            If a value eg. 5 is given, then it will only write out a .xyz file for every 5th timestep.
        """
        from ichor.core.files import PointsDirectory, PointsDirectoryParent, XYZ

        default_parent_suffix = PointsDirectoryParent._suffix
        default_points_dir_suffix = PointsDirectory._suffix

        # capitalize system name
        system_name = system_name.upper()

        root_path = Path(system_name).with_suffix(default_parent_suffix)

        # make root directory that will contain PointsDirectory-like dirs
        mkdir(root_path, empty=True)

        # make chunk directory
        chunk_idx = 0
        # this is the PointsDirectory
        inner_dir_name = f"{system_name}{chunk_idx}{default_points_dir_suffix}"
        mkdir(root_path / inner_dir_name, empty=True)

        # get only the every-th element of the trajectory
        geometries_to_write = self[::every]
        len_geoms_to_write = len(geometries_to_write)

        total_geom_counter = 0
        geom_counter = 0

        # loop over geometries and write to respective dir
        for i, atoms_instance in enumerate(geometries_to_write):

            if center:
                atoms_instance.centre()

            point_name = f"{system_name}{str(i).zfill(max(4, count_digits(len_geoms_to_write)))}.xyz"
            path = Path(point_name)
            path = root_path / inner_dir_name / path
            xyz_file = XYZ(path, atoms_instance)
            xyz_file.write()

            geom_counter += 1
            total_geom_counter += 1
            # if we have reached the split size, then make a new inner directory
            # do not make a new directory if last point is reached
            if geom_counter == split_size:

                # reset counter and update chunk
                geom_counter = 0
                chunk_idx += 1
                # make a new PointsDirectory-like directory
                inner_dir_name = f"{system_name}{chunk_idx}{default_points_dir_suffix}"
                if total_geom_counter != len_geoms_to_write:
                    mkdir(root_path / inner_dir_name, empty=True)

    def to_multiple_parent_dirs(
        self,
        system_name: str,
        split_size: int = 1000,
        nsplits_in_root: int = 5,
        every: int = 1,
        center=False,
    ):
        """Splits a trajectory into multiple parent directories, each of which
        can contain multiple PointsDirectory-like directories.

        :param system_name: name of system. This name will be used in the names
            of the files and directories which are made
        :param split_size: The number of .xyz files that inner PointsDirectory-like directory will contain, default 1000
        :param nsplits_in_root: The number of splits that are going to be in one root directory, default 5
            This would mean that there are 5 x 1000 geometries in that root directory.
        :param every:  An integer value that indicates the nth step at
            which an xyz file should be written, defaults to 1
        :param center: whether or not to subtract centroid of geometry before writing
            out xyz. Useful if geometries are far away from the origin
            which can result in Gaussian failing to write outputs properly, defaults to False
        """

        # TODO: simplify this so it uses to_dirs to prevent code duplication
        from ichor.core.files import PointsDirectory, PointsDirectoryParent, XYZ

        default_parent_suffix = PointsDirectoryParent._suffix
        default_points_dir_suffix = PointsDirectory._suffix

        # capitalize system name
        system_name = system_name.upper()

        # get only the every-th element of the trajectory
        geometries_to_write = self[::every]
        len_geoms_to_write = len(geometries_to_write)

        # parent directory index
        root_idx = 0
        # inner directory index
        chunk_idx = 0

        # add index to parent directory, because there will be multiple
        root_path = Path(f"{system_name}{root_idx}{default_parent_suffix}")
        # make initial root directory
        mkdir(root_path, empty=True)

        # make initial chunk directory, this is the PointsDirectory
        inner_dir_name = f"{system_name}{chunk_idx}{default_points_dir_suffix}"
        mkdir(root_path / inner_dir_name, empty=True)

        geoms_in_split_counter = 0
        nsplits_counter = 0

        # loop over geometries and write to respective dir
        for total_geom_counter, atoms_instance in enumerate(geometries_to_write):

            if center:
                atoms_instance.centre()

            point_name = f"{system_name}{str(total_geom_counter).zfill(max(4, count_digits(len_geoms_to_write)))}.xyz"
            path = Path(point_name)
            path = root_path / inner_dir_name / path
            xyz_file = XYZ(path, atoms_instance)
            xyz_file.write()

            geoms_in_split_counter += 1
            # if we have reached the split size, then make a new inner directory
            # do not make a new directory if last point is reached
            if geoms_in_split_counter == split_size:

                nsplits_counter += 1
                # reset counter and update chunk
                geoms_in_split_counter = 0
                chunk_idx += 1

                # make a new parent directory if the number of splits is reached
                if nsplits_counter == nsplits_in_root:

                    nsplits_counter = 0
                    root_idx += 1
                    root_path = root_path.with_name(
                        f"{system_name}{root_idx}{default_parent_suffix}"
                    )
                    # subtract 1 from geometries because otherwise will make an extra directory at the end
                    if total_geom_counter != len_geoms_to_write - 1:
                        mkdir(root_path, empty=True)

                inner_dir_name = f"{system_name}{chunk_idx}"
                # do not make a new directory on the last iteration
                # need to subtract 1 because otherwise they will be equal
                if total_geom_counter != len_geoms_to_write - 1:
                    mkdir(root_path / inner_dir_name, empty=True)

    @convert_to_path
    def split_traj(
        self, root_dir: Path = Path("split_trajectory"), split_size: int = 1000
    ):
        """Splits trajectory into sub-trajectories and writes then to a folder.
        Eg. a 10,000 original trajectory can be split into 10 sub-trajectories
        containing 1,000 geometries each (given a split size of 1,000).

        :param root_dir: The folder to write sub-trajectories to.
            Must be a Path object and this directory will be created internally.
        :param split_size: The split size by which to split original trajectory.
        """

        mkdir(root_dir, empty=True)
        chunks = [self[x : x + split_size] for x in range(0, len(self), split_size)]
        original_traj_stem = self.path.stem

        for idx, chunk in enumerate(chunks):
            new_traj_name = f"{original_traj_stem}_split{idx}.xyz"
            new_traj = Trajectory(root_dir / new_traj_name)
            new_traj.extend(chunk)
            new_traj.write()

    @convert_to_path
    def coordinates_to_xyz(
        self,
        fname: Path = Path("system_to_xyz.xyz"),
        step: int = 1,
    ):
        """write a new .xyz file that contains the timestep i, as well as the coordinates of the atoms
        for that timestep.

        :param fname: The file name to which to write the timesteps/coordinates
        :param step: Write coordinates for every n^th step. Default is 1, so writes coordinates for every step
        """
        return self.write(path=fname, every=step)

    @classmethod
    def features_file_to_trajectory(
        cls,
        f: Path,
        trajectory_path: Path,
        atom_types: List[str],
        header=0,
        index_col=0,
        sheet_name=0,
    ) -> "Trajectory":

        """Takes in a csv or excel file containing features and convert it to a `Trajectory` object.
        It assumes that the features start from the first column
        (column after the index column, if one exists). Feature files that are written out by ichor
        are in Bohr instead of Angstroms for now.

        After converting to cartesian coordinates, we have to convert
        Bohr to Angstroms because .xyz files are written out in Angstroms
        (and programs like Avogadro, VMD, etc. expect distances in angstroms).
        Failing to do that will result in xyz files that are in Bohr, so if features
        are calculated from them again, the features will be wrong.

        :param f: Path to the file (either .csv or .xlsx) containing the features.
            We only need the features for one atom to reconstruct the geometries,
            thus we only need 1 csv file or 1 sheet of an excel file.
            By default, the 0th sheet of the excel file is read in.
        :param atom_types: A list of strings corresponding to the atom elements (C, O, H, etc.).
            This has to be ordered the same way as atoms corresponding to the features.
        :param header: Whether the first line of the csv file contains the names of the columns.
            Default is set to 0 to use the 0th row.
        :param index_col: Whether a column should be used as the index column.
            Default is set to 0 to use 0th column.
        :param sheet_name: The excel sheet to be used to convert to xyz. Default is 0.
            This is only needed for excel files, not csv files.
        """

        f = Path(f)
        if f.suffix == ".xlsx":
            features_array = pd.read_excel(
                f, sheet_name=sheet_name, header=header, index_col=index_col
            ).values
        elif f.suffix == ".csv":
            features_array = pd.read_csv(f, header=header, index_col=index_col).values
        else:
            raise NotImplementedError("File needs to have .xlsx or .csv extension")

        n_features = 3 * len(atom_types) - 6

        features_array = features_array[:, :n_features]

        # xyz coordinates are currently in bohr, so convert them to angstroms
        xyz_array = alf_features_to_coordinates(features_array)
        xyz_array = bohr2ang * xyz_array

        trajectory = Trajectory(trajectory_path)
        trajectory.state = FileState.Read

        for geometry in xyz_array:
            # initialize empty Atoms instance
            atoms = Atoms()
            for ty, atom_coord in zip(atom_types, geometry):
                # add Atom instances for every atom in the geometry to the Atoms instance
                atoms.add(Atom(ty, atom_coord[0], atom_coord[1], atom_coord[2]))
            # Add the filled Atoms instance to the Trajectory instance and repeat for next geometry
            trajectory.add(atoms)

        return trajectory

    @classmethod
    def np_array_to_trajectory(
        self,
        arr: np.ndarray,
        trajectory_path: Union[str, Path],
        atom_types: List[str],
    ):
        """Creates a Trajectory instance from a np.ndarray object

        :param arr: np.ndarray containing features.This should be a 2D array of
            shape n_timesteps x n_features
        :param trajectory_path: The path associated with the trajectory instance which is made
        :param atom_types: A list of atom types (elements) that correspond to the features
            in the given array. It is important that they are the same order as in the np.ndarray.
        :return: Trajectory instance containing xyz geometries converted from features
        """

        xyz_array = alf_features_to_coordinates(arr)
        xyz_array = bohr2ang * xyz_array

        trajectory = Trajectory(trajectory_path)
        trajectory.state = FileState.Read

        for geometry in xyz_array:
            # initialize empty Atoms instance
            atoms = Atoms()
            for ty, atom_coord in zip(atom_types, geometry):
                # add Atom instances for every atom in the geometry to the Atoms instance
                atoms.add(Atom(ty, atom_coord[0], atom_coord[1], atom_coord[2]))
            # Add the filled Atoms instance to the Trajectory instance and repeat for next geometry
            trajectory.add(atoms)

        return trajectory

    @convert_to_path
    def change_atom_ordering(self, new_traj_name: Path, new_atom_ordering: List[int]):
        """Changes the atom ordering of the trajectory, given a list of how indices should be
        permuted and writes out a new trajectory file in the specified location.

        :param new_traj_name: Name of new trajectory file
        :param new_atom_ordering: A list of indices telling how to permute the current trajectory
        """

        if new_traj_name.suffix != ".xyz":
            new_traj_name = new_traj_name.with_suffix(".xyz")

        new_traj = Trajectory(new_traj_name)
        new_traj.state = FileState.Read

        for old_atoms_instance in self:
            new_atoms_instance = Atoms()
            for new_atom_idx in new_atom_ordering:
                new_atoms_instance.append(old_atoms_instance[new_atom_idx])
            new_traj.append(new_atoms_instance)

        return new_traj

    def split_packmol_trajectory(
        self, atoms_per_molecule: int, trajectory_name="packmol_traj_split.xyz"
    ):
        """Used to create packmol inputs"""

        new_traj = Trajectory(trajectory_name)

        for batch in chunker(self[0], atoms_per_molecule):

            atoms = Atoms(batch)
            new_traj.append(atoms)

        new_traj.write()

    def _write_file(self, path: Path, every: int = 1, center: bool = False):
        """Write  a trajectory file to a given location.

        :param path: Path to trajectory file
        :param every: Write every nth point. Default is 1, so every point is written.
        :param center: Whether to center the geometries prior to writing. This centers the geometry on the
            centroid of the molecule. This is helpful, so that x,y,z coordinates are in the same range
            (i.e. the molecule does not float around in space too much.)
        """

        write_str = ""

        for i, atoms_instance in enumerate(self):
            if (i % every) == 0:
                if center:
                    atoms_instance.centre()
                write_str += f"{len(atoms_instance)}\n"
                write_str += f"i = {i}\n"
                for atom in atoms_instance:
                    write_str += (
                        f"{atom.type} {atom.x:16.8f} {atom.y:16.8f} {atom.z:16.8f}\n"
                    )

        return write_str

    def __getitem__(self, item) -> Atoms:
        """Used to index a Trajectory instance by a str (eg. trajectory['C1']) or by integer (eg. trajectory[2]),
        remember that indeces in Python start at 0, so trajectory[2] is the 3rd timestep.
        You can use something like (np.array([traj[i].features for i in range(2)]).shape) to features of a slice of
        a trajectory as slice is not implemented in __getitem__"""
        if self.state is not FileState.Read:
            self.read()

        # if ListOfAtoms instance is indexed by an integer or np.int64, then index as a list
        if isinstance(item, (int, np.int64)):
            return list.__getitem__(self, item)

        # if ListOfAtoms is indexed by a string, such as an atom name (eg. C1, H2, O3, H4, etc.)
        elif isinstance(item, str):
            from ichor.core.atoms.list_of_atoms_atom_view import AtomView

            return AtomView(self, item)

        # if PointsDirectory is indexed by a slice e.g. [:50], [20:40], etc.
        elif isinstance(item, slice):

            new_traj = Trajectory(self.path, list.__getitem__(self, item))
            # need to set the filestate to read otherwise the file will be read again
            new_traj.state = FileState.Read

            return new_traj

        # if PointsDirectory is indexed by a list, e.g. [0, 5, 10]
        elif isinstance(item, (list, np.ndarray)):

            new_traj = Trajectory(self.path, [list.__getitem__(self, i) for i in item])
            # need to set the filestate to read otherwise the file will be read again
            new_traj.state = FileState.Read

            return Trajectory(self.path, [list.__getitem__(self, i) for i in item])

        # if indexing by something else that has not been programmed yet
        # should only be reached if not indexed by int, str, or slice
        raise TypeError(
            f"Cannot index type '{self.__class__.__name__}' with type '{type(item)}"
        )

    def __iter__(self) -> Iterable[Atoms]:
        """Used to iterate over timesteps (Atoms instances) in places such as for loops"""
        if self.state is not FileState.Read:
            self.read()
        return super().__iter__()

    def __len__(self):
        """Returns the number of timesteps in the Trajectory instance"""
        if self.state is not FileState.Read:
            self.read()
        return super().__len__()

    def __repr__(self) -> str:
        """Make a repr otherwise doing print(trajectory_instance) will print
        out an empty list if the trajectory attributes have not been accessed yet,
        due to how how the files are being parsed using PathObject/File classes."""
        return (
            f"class {self.__class__}\n"
            f"xyz_file: {self.path or None}\n"
            f"atom_names: {self.atom_names}\n"
            f"trajectory_coordinates_shape (n_timesteps, n_atoms, 3): {self.coordinates.shape}\n"
        )
