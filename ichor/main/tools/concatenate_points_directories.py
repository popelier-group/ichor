from ichor.files import PointsDirectory
from pathlib import Path
from ichor.globals import GLOBALS


def recurssive_rename(dir: Path, orig: str, updated: str):
    for f in dir.iterdir():
        if orig in f.name:
            newf = Path(str(f).replace(f.name, f.name.replace(orig, updated)))
            f.rename(newf)
        if f.is_dir():
            recurssive_rename(f, orig, updated)


def concatenate_points_directories(pd1: Path, pd2: Path) -> PointsDirectory:
    pd2 = PointsDirectory(pd2)
    for point in pd2:
        points = PointsDirectory(pd1)
        new_name = f"{GLOBALS.SYSTEM_NAME}{str(len(points) + 1).zfill(4)}"
        new_directory =  pd1 / new_name
        point.move(new_directory)
        recurssive_rename(new_directory, point.path.name, new_name)
    return PointsDirectory(pd1)


def concatenate_points_directories_menu() -> PointsDirectory:
    from ichor.analysis.get_path import get_dir
    print("Enter location of 1st PointsDirectory: ")
    pd1 = get_dir(Path())
    print("Enter location of 2nd PointsDirectory: ")
    pd2 = get_dir(Path())
    return concatenate_points_directories(pd1, pd2)
