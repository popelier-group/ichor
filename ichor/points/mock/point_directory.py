from pathlib import Path

from ichor.points.point_directory import PointDirectory


class MockPointDirectory(PointDirectory):
    def __init__(self, path: Path):
        self.path = path
