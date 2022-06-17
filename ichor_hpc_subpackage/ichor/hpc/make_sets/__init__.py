import inspect
import sys
from typing import List, Any, Optional, Tuple

from ichor.hpc.make_sets.make_set_method import MakeSetMethod
from ichor.hpc.make_sets.min_max import MinMax
from ichor.hpc.make_sets.min_max_mean import MinMaxMean
from ichor.hpc.make_sets.random_points import RandomPoints
from pathlib import Path
from ichor.core.files import PointsDirectory, Trajectory, XYZ
from ichor.core.atoms import ListOfAtoms
from ichor.core.common.io import mkdir
from ichor.core.common.int import count_digits


# todo: improve typehint
def get_make_set_methods() -> List[Any]:
    """Returns a list of classes which are used to initialize a training set. These are classes such as MinMaxMean, RandomPoints, etc."""

    return [
        obj
        for _, obj in inspect.getmembers(
            sys.modules[__name__], inspect.isclass
        )
        if issubclass(obj, MakeSetMethod)
    ]

def make_sets_npoints(
    points: ListOfAtoms, set_size: int, methods: List[str]
) -> int:
    """Return the total number of points that are going to be used to initialize the training set. Multiple initialization methods
    can be combined to give the total number of initial training points."""

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
    from ichor.hpc import FILE_STRUCTURE, GLOBALS

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
        write_set_to_dir(FILE_STRUCTURE["training_set"], training_set)

    if make_sample_pool:
        if sample_pool_size is None:
            sample_pool_size = GLOBALS.SAMPLE_POINTS
        if sample_pool_method is None:
            sample_pool_method = GLOBALS.SAMPLE_POOL_METHOD
        sample_pool, points = make_set(
            points, sample_pool_size, sample_pool_method
        )
        write_set_to_dir(FILE_STRUCTURE["sample_pool"], sample_pool)

    if make_validation_set:
        if validation_set_size is None:
            validation_set_size = GLOBALS.VALIDATION_POINTS
        if validation_set_method is None:
            validation_set_method = GLOBALS.VALIDATION_SET_METHOD
        validation_set, _ = make_set(
            points, validation_set_size, validation_set_method
        )
        write_set_to_dir(FILE_STRUCTURE["validation_set"], validation_set)


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
    from ichor.hpc import GLOBALS

    mkdir(path)
    for i, point in enumerate(points):
        point_name = f"{GLOBALS.SYSTEM_NAME}{str(i+1).zfill(max(4, count_digits(len(points))))}"
        mkdir(path / point_name)
        xyz = XYZ(
            path / point_name / f"{point_name}{XYZ.filetype}", atoms=point
        )
        xyz.atoms.centre()
        xyz.write()


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
