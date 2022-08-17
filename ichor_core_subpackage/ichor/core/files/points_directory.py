from pathlib import Path
from typing import Union, List, Optional, Dict, Callable
from ichor.core.atoms import ListOfAtoms, Atoms
from ichor.core.common.io import mkdir
from ichor.core.files import Directory
from ichor.core.files import PointDirectory
from ichor.core.files import GJF
from ichor.core.files import XYZ
import numpy as np
from ichor.core.calculators.alf import default_alf_calculator
from ichor.core.atoms import ALF
from ichor.core.common.dict import merge
from ichor.core.files import PointsDirectoryProperties


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
    Each of the subdirectories contains Gaussian files (such as .gjf), as well as an `atomic_files` directory, which then contains the AIMALL files.
    A `PointsDirectory` will wrap around the whole TRAINING_SET directory (which contains multiple points), while a `PointDirectory`
    will wrap around a SYSTEM_NAME00... folder (which only contains information about 1 point).

    :param path: Path to a directory which contains points. This path is typically the path to the training set, sample pool, etc.
    """

    def __init__(self, path: Union[Path, str], needs_parsing = True, *args, **kwargs):
        # Initialise `list` parent class of `ListOfAtoms`
        ListOfAtoms.__init__(self,  *args, **kwargs)
        if needs_parsing:
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

        # iterdir sorts by name, see Directory class
        for f in self.iterdir():
            # if the current PathObject is a directory that matches
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
        self = self.sort(key=lambda x: x.path.name)

    def connectivity(self, connectivity_calculator: Callable[..., np.ndarray]) -> np.ndarray:
        """Return the connectivity matrix (n_atoms x n_atoms) for the given Atoms instance.

        Returns:
            :type: `np.ndarray` of shape n_atoms x n_atoms
        """

        return connectivity_calculator(self[0].atoms)
    
    def alf(self, alf_calculator: Callable[..., ALF], *args, **kwargs) -> List[ALF]:
        """Returns the Atomic Local Frame (ALF) for all Atom instances that are held in Atoms
        e.g. [[0,1,2],[1,0,2], [2,0,1]]
        :param *args: positional arguments to pass to alf calculator
        :param **kwargs: key word arguments to pass to alf calculator
        """
        return [alf_calculator(atom_instance, *args, **kwargs) for atom_instance in self[0].atoms]

    def properties(self, system_alf: Optional[List[ALF]] = None, specific_property: str = None) -> PointsDirectoryProperties:
        """ Get properties contained in the PointDirectory. IF no system alf is passed in, an automatic process to get C matrices is started.
        
        :param system_alf: Optional list of `ALF` instances that can be passed in to use a specific alf instead of automatically trying to compute it.
        :param key: return only a specific key from the returned PointsDirectoryProperties dictionary
        """
        
        if not system_alf:
            # TODO: The default alf calculator (the cahn ingold prelog one) should accept connectivity, not connectivity calculator, so connectivity also needs to be passed in.
            system_alf = self.alf(default_alf_calculator)
        
        points_dir_properties = {}
        
        for point in self:
            points_dir_properties[point.name] = point.properties(system_alf)
        
        points_dir_properties = PointsDirectoryProperties(points_dir_properties)
        
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
        error = OrderedDict(sorted(error.items()))

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
                    
    def __getitem__(
        self, item: Union[int, str]
    ) -> Union[Atoms, ListOfAtoms]:
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
            
            return PointsDirectory(self.path, False, [list.__getitem__(self, i) for i in item])

        # if indexing by something else that has not been programmed yet, should only be reached if not indexed by int, str, or slice
        raise TypeError(
            f"Cannot index type '{self.__class__.__name__}' with type '{type(item)}"
        )