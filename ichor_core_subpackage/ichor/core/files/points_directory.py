import re
from pathlib import Path
from typing import Union, Set

from ichor.core.atoms import ListOfAtoms
from ichor.core.common.functools import buildermethod
from ichor.core.common.io import mkdir
from ichor.core.common.sorting.natsort import ignore_alpha, natsorted
from ichor.core.files import Directory
from ichor.core.files.point_directory import PointDirectory
from ichor.core.files.gjf import GJF
from ichor.core.files.xyz import XYZ
import numpy as np
from typing import Optional


class PointsDirectory(ListOfAtoms, Directory):
    """A helper class that wraps around a directory which contains points (molecules with various geometries).
    Calling Directory.__init__(self, path) will call the `parse` method of PointsDirectory instead of Directory
    (because Python looks for the method in this class first before looking at parent class methods.) A typical ICHOR
    directory that contains points will points will have a structure like this:
    -TRAINING_SET
        -- SYSTEM_NAME001
        -- SYSTEM_NAME002
        -- SYSTEM_NAME003
        ........
    Each of the subdirectories contains Gaussain files (such as .gjf), as well as an `atomic_files` directory, which then contains the AIMALL files.
    A `PointsDirectory` will wrap around the whole TRAINING_SET directory (which contains multiple points), while a `PointDirectory`
    will wrap around a SYSTEM_NAME00... folder (which only contains information about 1 point).

    :param path: Path to a directory which contains points. This path is typically the path to the training set, sample pool, etc.
    """

    def __init__(self, path: Union[Path, str]):
        # Initialise `list` parent class of `ListOfAtoms`
        ListOfAtoms.__init__(self)
        # this will call Directory __init__ method (which then calls self.parse)
        # since PointsDirectory implements a `parse` method, it will be called instead of the Directory parse method
        Directory.__init__(self, path)

    def _parse(self) -> None:
        """
        Called from Directory.__init__(self, path)
        Parse a directory (such as TRAINING_SET, TEST_SET,etc.) and make PointDirectory objects of each of the subirectories.
        If however there are only .gjf files present in the directory at the moment, then make a new directory for each .gjf file
        and move the .gjf file in there. So for example, if there is a file called WATER001.gjf, this method will make a
        folder called WATER001 and will move WATER001.gjf in it.
        Initially when the training set, test set, and sample pool directories are made, there are only .gjf files present in the
        directory. This method makes them in separate directories.
        """

        # if current instance is empty, then iterate over the contents of the directory (see __iter__ method below)
        for f in self:
            # if the current PathObject is a directory that matches the given regex pattern, then wrap the directory in
            # a PointDirectory instance and add to self
            if PointDirectory.check_path(f):
                point = PointDirectory(f)
                if not point.should_ignore:
                    self.append(point)
            elif f.is_file() and f.suffix in {XYZ.filetype, GJF.filetype}:
                new_dir = self.path / f.stem
                mkdir(new_dir)
                f.replace(new_dir / f.name)
                self.append(
                    PointDirectory(new_dir)
                )  # wrap the new directory as a PointDirectory instance and add to self
        # sort by the names of the directories (by the numbers in their name) since the system name is always the same
        self.sort(key=lambda x: x.path.name)

    @buildermethod
    def read(self):
        """Read each of the PointDirectory instances inside a PointsDirectory instance and store relevant information into attributes.

        .. note::
            This method does not need to be called explicitly because if an the state of the file is `FileState.Unread` and the attribute
            does not exist, the `__getattribute__` method defined in `class PathObject` will be called which automatically reads the file
            if a non existing attribute is being accessed.
        """
        for point in self:
            point.read()

    def dump(self):
        for point in self:
            point.dump()

    def iterdir(self):
        return iter(natsorted(super().iterdir(), key=ignore_alpha))

    @property
    def types(self):
        """Returns the atom elements for atoms, assumes each timesteps has the same atoms.
        Removes duplicates."""
        return self[0].atoms.types
    
    @property
    def types_extended(self):
        """Returns the atom elements for atoms, assumes each timesteps has the same atoms.
        Removes duplicates."""
        return self[0].atoms.types_extended

    @property
    def atom_names(self):
        """Return the atom names from the first timestep. Assumes that all timesteps have the same
        number of atoms/atom names."""
        return self[0].atoms.atom_names

    @property
    def natoms(self):
        """ Returns the number of atoms in the first timestep. Each timestep should have the same number of atoms."""
        return len(self[0].atoms)

    @property
    def coordinates(self) -> np.ndarray:
        """
        Returns:
            :type: `np.ndarray`
            the xyz coordinates of all atoms for all timesteps. Shape `n_timesteps` x `n_atoms` x `3`
        """
        return np.array([timestep.atoms.coordinates for timestep in self])

    @property
    def connectivity(self) -> np.ndarray:
        """ Returns the connectivity matrix of the first timestep."""

        return self[0].atoms.connectivity

    @property
    def alf(self) -> np.ndarray:
        """ Returns the atomic local frame for the first timestep."""
        return self[0].atoms.alf

    def coordinates_to_xyz(
        self, fname: Optional[Union[str, Path]] = Path("system_to_xyz.xyz"), step: Optional[int] = 1
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
        """write a new .xyz file that contains the timestep i, as well as the coordinates of the atoms
        for that timestep. The comment lines in the xyz have absolute predictions errors. These can then be plotted in
        ALFVisualizer as cmap to see where poor predictions happen.

        :param models_path: The model path to one atom.
        :param property_: The property for which to predict for and get errors (iqa or any multipole moment)
        :param fname: The file name to which to write the timesteps/coordinates
        :param step: Write coordinates for every n^th step. Default is 1, so writes coordinates for every step
        """
        from collections import OrderedDict

        from ichor.core.analysis.predictions import get_true_predicted
        from ichor.core.constants import ha_to_kj_mol
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
        error = OrderedDict(sorted(error.items()))

        system_name = models.system

        fname = fname.with_suffix(".xyz")

        with open(fname, "w") as f:
            for i, point in enumerate(self[::step]):
                # this is used when self is a PointsDirectory, so you are iterating over PointDirectory instances

                # {atom_name : {prop1: val, prop2: val}, atom_name2: {prop1: val, prop2: val}, ....} for one timestep
                dict_to_write = {
                    outer_k: {
                        inner_k: inner_v[i]
                        for inner_k, inner_v in outer_v.items()
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

    def __iter__(self):
        """
        This method is called when iterating over an instance of `PointsDirectory`. If the current instance is empty (i.e. its length is 0),
        then iterate over the directory set as `self.path` (`self.path` attribute is inherited from PathObject and because PointsDirectory
        subclasses from Directory and the Directory `__init__` method is called, then the PointsDirectory object will
        also have this attribute). If the current instance is not empty, then iterate over the `PointDirectory` objects
        which are in `self`. Because `PointsDirectory` inherits from Points, which
        inherits from `ListofAtoms` (which subsequently inherits from `list`), then `self` can be used as a list itself.
        """
        if len(self) == 0:
            return Directory.__iter__(self)
        else:
            return ListOfAtoms.__iter__(self)

    def __getattr__(self, item):
        try:
            return [getattr(point, item) for point in self]
        except AttributeError:
            raise AttributeError(
                f"'{self.__class__.__name__}' has no attribute '{item}'"
            )
