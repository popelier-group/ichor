from pathlib import Path

from ichor.ichor_lib.common.io import cp, mkdir
from ichor.ichor_lib.files import PointsDirectory
from ichor.ichor_hpc.globals import GLOBALS


def recursive_rename(
    dir: Path, orig: str, updated: str, verbose: bool = False
):
    for f in dir.iterdir():
        if orig in f.name:
            newf = Path(str(f).replace(f.name, f.name.replace(orig, updated)))
            if verbose:
                print(f"Renaming '{f}' to '{newf}'")
            f.rename(newf)
        if f.is_dir():
            recursive_rename(f, orig, updated)


def concatenate_points_directories(
    pd1: Path, pd2: Path, verbose: bool = False
) -> PointsDirectory:
    pd2 = PointsDirectory(pd2)
    for point in pd2:
        points = PointsDirectory(pd1)
        new_name = f"{GLOBALS.SYSTEM_NAME}{str(len(points) + 1).zfill(4)}"
        new_directory = pd1 / new_name
        if verbose:
            print(f"Copying '{point.path}' to '{new_directory}'")
        mkdir(new_directory)
        cp(point.path, new_directory)
        recursive_rename(
            new_directory, point.path.name, new_name, verbose=verbose
        )
    return PointsDirectory(pd1)


def concatenate_points_directories_menu(
    verbose: bool = True,
) -> PointsDirectory:
    from ichor.ichor_lib.analysis.get_path import get_dir

    print("Enter location of 1st PointsDirectory: ")
    pd1 = get_dir(Path())
    print("Enter location of 2nd PointsDirectory: ")
    pd2 = get_dir(Path())
    return concatenate_points_directories(pd1, pd2, verbose=verbose)
