from ichor.points.mock.path import MockPath
from ichor.points.mock.point_directory import MockPointDirectory
from ichor.points.points_directory import PointsDirectory


class MockPointsDirectory(PointsDirectory):
    def __init__(self, path: MockPath):
        for i in range(path.nfiles):
            self.append(
                MockPointDirectory(path / f"MOCK_POINT{str(i+1).zfill(4)}")
            )
