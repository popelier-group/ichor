from ichor.common.functools import buildermethod
from ichor.files import Directory
from ichor.points.point_directory import PointDirectory
from ichor.points.points import Points
from ichor.common.io import mkdir
from pathlib import Path


class PointsDirectory(Points, Directory):
    def __init__(self, path):
        Points.__init__(self)
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
