from pathlib import Path
from typing import Optional

from ichor.core.files import PointsDirectory
from ichor.core.menu import PathCompleter
from ichor.core.menu import Menu, MenuVar
from ichor.hpc.make_sets import make_training_set, make_sample_pool, make_validation_set, make_sets


def set_points_location(points_location: MenuVar[Path]):
    with PathCompleter():
        points_location.var = input("Enter Points Location: ")


def find_points_location() -> Optional[Path]:
    from ichor.hpc import GLOBALS
    if GLOBALS.POINTS_LOCATION is not None and GLOBALS.POINTS_LOCATION.exists():
        return GLOBALS.POINTS_LOCATION
    for f in Path(".").iterdir():
        if f.suffix == ".xyz":
            return f
    for d in Path(".").iterdir():
        if d.is_dir() and len(PointsDirectory(d)) > 1:
            return d


def make_sets_menu():
    points_location = MenuVar("Points Location", find_points_location())
    with Menu("Make Set Menu") as menu:
        menu.add_option(
            "1",
            "Make Training Set",
            make_training_set,
            kwargs={"points_input": points_location},
        )
        menu.add_option(
            "2",
            "Make Sample Pool",
            make_sample_pool,
            kwargs={"points_input": points_location},
        )
        menu.add_option(
            "3",
            "Make Validation Set",
            make_validation_set,
            kwargs={"points_input": points_location},
        )
        menu.add_space()
        menu.add_option(
            "a",
            "Make All Sets",
            make_sets,
            kwargs={"points_input": points_location},
        )
        menu.add_space()
        menu.add_option("p", "Choose points location", set_points_location, args=[points_location])
        menu.add_space()
        menu.add_var(points_location)
