from pathlib import Path

from ichor.common.functools import buildermethod
from ichor.common.io import mkdir
from ichor.files import Directory
from ichor.points.point_directory import PointDirectory
from ichor.points.points import Points


class PointsDirectory(Points, Directory):
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
        These paths are defined in GLOBALS.
    """
    def __init__(self, path):
        # matt_todo: Points does not have __init__, so don't think this is needed
        Points.__init__(self)
        # this will call Directory __init__ method (which then calls self.parse)
        # since PointsDirectory also implements a `parse` method, it will be called instead of the Directory parse method
        Directory.__init__(self, path)

    def parse(self) -> None:
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
            if f.is_dir() and PointDirectory.dirpattern.match(f.name):
                self += [PointDirectory(f)]
            # otherwise if the PathObject is a file that ends in .gjf, make a new directory with its path set to self.path/f.stem
            # for example if the given path is ./TRAINING_SET/ and there is WATER001.gjf, it will make ./TRANING_SET/WATER001/
            elif f.is_file() and f.suffix == ".gjf":
                new_dir = self.path / f.stem
                mkdir(new_dir)
                f.replace(new_dir / f.name)
                self += [PointDirectory(new_dir)]  # wrap the new directory as a PointDirectory instance and add to self
        # sort by the names of the directories (by the numbers in their name) since the system name is always the same
        self.sort(key=lambda x: x.path.name)

    @buildermethod
    def read(self) -> "PointsDirectory":
        """Read each of the PointDirectory instances inside a PointsDirectory instance and store relevant information into attributes.

        .. note::
            This method does not need to be called explicitly because if an the state of the file is `FileState.Unread` and the attribute
            does not exist, the `__getattribute__` method defined in `class PathObject` will be called which automatically reads the file
            if a non existing attribute is being accessed.
        """
        for point in self:
            point.read()

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
            return Points.__iter__(self)
