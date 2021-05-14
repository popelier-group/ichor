from ichor.common.functools import buildermethod
from ichor.files import Directory, FileState
from ichor.points.point_directory import PointDirectory
from ichor.points.points import Points


class PointsDirectory(Points, Directory):
    def __init__(self, path):
        Points.__init__(self)
        Directory.__init__(self, path)

    def parse(self) -> None:
        for f in self:
            if f.is_dir() and PointDirectory.dirpattern.match(f.name):
                self += [PointDirectory(f)]
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
