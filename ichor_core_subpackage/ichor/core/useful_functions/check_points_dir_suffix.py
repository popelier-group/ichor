from ichor.core.files import PointsDirectoryParent


def single_or_many_points_directories(pd_path):
    """Checks whether the current selected PointsDirectory path is a directory containing
    many PointsDirectories, or is just one PointsDirectory.

    This is just done by checking if parent is in the name of the directory.
    """

    if PointsDirectoryParent._suffix == pd_path.suffix:
        return True
    return False
