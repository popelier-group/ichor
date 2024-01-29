import ichor.cli.global_menu_variables
from ichor.core.files import PointsDirectoryParent


def single_or_many_points_directories():
    """Checks whether the current selected PointsDirectory path is a directory containing
    many PointsDirectories, or is just one PointsDirectory.

    This is just done by checking if parent is in the name of the directory.
    """

    if (
        PointsDirectoryParent._suffix
        in ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH.stem.lower()
    ):
        return True
    return False
