import inspect
import sys
from pathlib import Path
from typing import Any, List, Optional, Tuple

from ichor.atoms import ListOfAtoms
from ichor.files import Trajectory, GJF
from ichor.make_sets.make_set_method import MakeSetMethod
from ichor.make_sets.min_max import MinMax
from ichor.make_sets.min_max_mean import MinMaxMean
from ichor.make_sets.random import RandomPoints
from ichor.menu import Menu
from ichor.points import PointsDirectory
from ichor.common.io import mkdir
from ichor.common.int import count_digits
from ichor.tab_completer import PathCompleter

__all__ = ["make_sets", "make_sets_menu", "make_sets_npoints"]


POINTS_LOCATION: Optional[Path] = None


def get_make_set_methods() -> List[Any]:
    return [
        obj
        for _, obj in inspect.getmembers(
            sys.modules[__name__], inspect.isclass
        )
        if issubclass(obj, MakeSetMethod)
    ]


def make_sets_npoints(points: ListOfAtoms, set_size: int, methods: List[str]) -> int:
    npoints = 0
    for method in methods:
        for MakeSet in get_make_set_methods():
            if method == MakeSet.name():
                npoints += MakeSet.get_npoints(set_size, points)
    return npoints


def make_sets(
    points_input: Path,
    make_training_set: bool = True,
    training_set_size: Optional[int] = None,
    training_set_method: Optional[List[str]] = None,
    make_sample_pool: bool = True,
    sample_pool_size: Optional[int] = None,
    sample_pool_method: Optional[List[str]] = None,
    make_validation_set: bool = True,
    validation_set_size: Optional[int] = None,
    validation_set_method: Optional[List[str]] = None,
) -> None:
    from ichor.globals import GLOBALS

    if points_input.suffix == ".xyz":
        points = Trajectory(points_input)
    elif points_input.is_dir():
        points = PointsDirectory(points_input)
    else:
        raise TypeError(
            f"Cannot convert path '{points_input}' into type 'ListOfAtoms'"
        )

    if make_training_set:
        if training_set_size is None:
            training_set_size = GLOBALS.TRAINING_POINTS
        if training_set_method is None:
            training_set_method = GLOBALS.TRAINING_SET_METHOD
        training_set, points = make_set(
            points, training_set_size, training_set_method
        )
        write_set_to_dir(GLOBALS.FILE_STRUCTURE["training_set"], training_set)

    if make_sample_pool:
        if sample_pool_size is None:
            sample_pool_size = GLOBALS.SAMPLE_POINTS
        if sample_pool_method is None:
            sample_pool_method = GLOBALS.SAMPLE_POOL_METHOD
        sample_pool, points = make_set(
            points, sample_pool_size, sample_pool_method
        )
        write_set_to_dir(GLOBALS.FILE_STRUCTURE["sample_pool"], sample_pool)

    if make_validation_set:
        if validation_set_size is None:
            validation_set_size = GLOBALS.VALIDATION_POINTS
        if validation_set_method is None:
            validation_set_method = GLOBALS.VALIDATION_SET_METHOD
        validation_set, _ = make_set(
            points, validation_set_size, validation_set_method
        )
        write_set_to_dir(GLOBALS.FILE_STRUCTURE["validation_set"], validation_set)


def make_set(
    points: ListOfAtoms, npoints: int, methods: List[str]
) -> Tuple[ListOfAtoms, ListOfAtoms]:
    new_set = ListOfAtoms()
    for method in methods:
        for MakeSet in get_make_set_methods():
            if method == MakeSet.name():
                method = (
                    MakeSet(npoints)
                    if hasattr(MakeSet, "npoints")
                    else MakeSet()
                )
                points_for_set, points = make_set_with_method(points, method)
                new_set += points_for_set
                break
        else:
            raise ValueError(f"Cannot find method '{method}'")
    return new_set, points


def write_set_to_dir(path: Path, points: ListOfAtoms) -> None:
    from ichor.globals import GLOBALS
    mkdir(path)
    for i, point in enumerate(points):
        point_name = f"{GLOBALS.SYSTEM_NAME}{str(i+1).zfill(max(4, count_digits(len(points))))}"
        mkdir(path / point_name)
        gjf = GJF(path / point_name / f"{point_name}.gjf")
        gjf.atoms = point
        gjf.write()


def make_set_with_method(
    points: ListOfAtoms, method: MakeSetMethod
) -> Tuple[ListOfAtoms, ListOfAtoms]:
    points_to_get = list(
        set(method.get_points(points))
    )  # Get points and remove duplicates
    new_set = ListOfAtoms()
    for i in sorted(points_to_get, reverse=True):
        new_set += [points[i]]
        del points[i]
    return new_set, points


def set_points_location():
    global POINTS_LOCATION
    with PathCompleter():
        POINTS_LOCATION = input("Enter Points Location: ")


def make_training_set(points_input: Path) -> None:
    make_sets(
        points_input,
        make_training_set=True,
        make_sample_pool=False,
        make_validation_set=False,
    )


def make_sample_pool(points_input: Path) -> None:
    make_sets(
        points_input,
        make_training_set=False,
        make_sample_pool=True,
        make_validation_set=False,
    )


def make_validation_set(points_input: Path) -> None:
    make_sets(
        points_input,
        make_training_set=False,
        make_sample_pool=False,
        make_validation_set=True,
    )


def make_sets_menu_refresh(menu):
    menu.clear_options()
    menu.add_option(
        "1",
        "Make Training Set",
        make_training_set,
        kwargs={"points_input": POINTS_LOCATION},
    )
    menu.add_option(
        "2",
        "Make Sample Pool",
        make_sample_pool,
        kwargs={"points_input": POINTS_LOCATION},
    )
    menu.add_option(
        "3",
        "Make Validation Set",
        make_validation_set,
        kwargs={"points_input": POINTS_LOCATION},
    )
    menu.add_space()
    menu.add_option(
        "a",
        "Make All Sets",
        make_sets,
        kwargs={"points_input": POINTS_LOCATION},
    )
    menu.add_space()
    menu.add_option("p", "Choose points location", set_points_location)
    menu.add_space()
    menu.add_message(f"Points Location: {POINTS_LOCATION}")
    menu.add_final_options()


def find_points_location() -> Optional[Path]:
    for f in Path(".").iterdir():
        if f.suffix == ".xyz":
            return f
    for d in Path(".").iterdir():
        if d.is_dir() and len(PointsDirectory(d)) > 1:
            return d


def make_sets_menu():
    global POINTS_LOCATION
    POINTS_LOCATION = find_points_location()
    with Menu("Make Set Menu", refresh=make_sets_menu_refresh):
        pass
