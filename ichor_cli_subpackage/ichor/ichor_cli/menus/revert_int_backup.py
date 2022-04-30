from pathlib import Path
from typing import List

from ichor_hpc.file_structure.file_structure import FILE_STRUCTURE
from ichor.ichor_lib.files import INTs, PointsDirectory
from ichor.menus.menu import Menu


def revert_ints_backup(ints_dir: Path):
    ints = INTs(ints_dir)
    ints.revert_backup()


def revert_points_directory_backup(points_directory_path: Path):
    points = PointsDirectory(points_directory_path)
    for point in points:
        if point.ints.exists():
            revert_ints_backup(point.ints.path)


def revert_point_directories(paths: List[Path]):
    for path in paths:
        revert_points_directory_backup(path)


def revert_int_bak_menu():
    with Menu(
        "Revert INTs Backup Menu", space=True, back=True, exit=True
    ) as menu:
        menu.add_option(
            "ts",
            f"Revert {FILE_STRUCTURE['training_set']}",
            revert_points_directory_backup,
            kwargs={"points_directory_path": FILE_STRUCTURE["training_set"]},
        )
        menu.add_option(
            "sp",
            f"Revert {FILE_STRUCTURE['sample_pool']}",
            revert_points_directory_backup,
            kwargs={"points_directory_path": FILE_STRUCTURE["sample_pool"]},
        )
        menu.add_option(
            "vs",
            f"Revert {FILE_STRUCTURE['validation_set']}",
            revert_points_directory_backup,
            kwargs={"points_directory_path": FILE_STRUCTURE["validation_set"]},
        )
        menu.add_space()
        menu.add_option(
            "a",
            "Revert all of the above",
            revert_point_directories,
            {
                "paths": [
                    FILE_STRUCTURE["training_set"],
                    FILE_STRUCTURE["sample_pool"],
                    FILE_STRUCTURE["validation_set"],
                ]
            },
        )
