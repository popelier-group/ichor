from ichor.files import PointsDirectory
from pathlib import Path
from ichor.globals import GLOBALS


def concatenate_points_directories(pd1: Path, pd2: Path) -> PointsDirectory:
    pd2 = PointsDirectory(pd2)
    for point in pd2:
        points = PointsDirectory(pd1)
        new_directory = (
                pd1
                / f"{GLOBALS.SYSTEM_NAME}{str(len(points) + 1).zfill(4)}"
        )
        point.move(new_directory)
    return PointsDirectory(pd1)


def concatenate_points_directories_menu() -> PointsDirectory:
    from ichor.analysis.get_path import get_dir
    print("Enter location of 1st PointsDirectory: ")
    pd1 = get_dir(Path())
    print("Enter location of 2nd PointsDirectory: ")
    pd2 = get_dir(Path())
    return concatenate_points_directories(pd1, pd2)
