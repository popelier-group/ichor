from pathlib import Path

from ichor.common.functools import buildermethod
from ichor.common.io import mkdir
from ichor.files import Directory
from ichor.points.point_directory import PointDirectory
from ichor.points.points import Points


class PointsDirectory(Points, Directory):
    """A helper class that wraps around a directory which contains points (molecules with various geometries)

    :param path: Path to a directory which contains points. This path is typically the path to the training set, sample pool, etc. These paths are defined in GLOBALS.
    """
    def __init__(self, path):
        Points.__init__(self)  # matt_todo: Points does not have __init__, so don't think this is needed
        Directory.__init__(self, path)

    def parse(self) -> None:
        for f in self:
            if f.is_dir() and PointDirectory.dirpattern.match(f.name):
                self += [PointDirectory(f)]
            elif f.is_file() and f.suffix == ".gjf":
                new_dir = self.path / f.stem
                mkdir(new_dir)
                f.replace(new_dir / f.name)
                self += [PointDirectory(new_dir)]
        self.sort(key=lambda x: x.path.name)

    @buildermethod
    def read(self) -> "PointsDirectory":
        for point in self:
            point.read()

    def __iter__(self):
        if len(self) == 0:
            return Directory.__iter__(self)
        else:
            return Points.__iter__(self)
