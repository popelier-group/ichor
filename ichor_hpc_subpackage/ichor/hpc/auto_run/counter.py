from pathlib import Path
from typing import Optional, Tuple

from ichor.core.common.io import mkdir, remove

_counter_location = None


def _check_counter_location():
    from ichor.hpc import FILE_STRUCTURE
    global _counter_location
    if _counter_location is None:
        _counter_location = FILE_STRUCTURE["counter"]


def get_counter_location(counter_location: Optional[Path] = None) -> Path:
    _check_counter_location()
    counter_location = counter_location or _counter_location

    if counter_location.is_dir():
        counter_location = counter_location / _counter_location

    return counter_location


def read_counter(
    counter_location: Optional[Path] = None, must_exist: bool = True
) -> Tuple[int, int]:
    """Reads the counter file, returns current iteration and max iteration"""
    from ichor.hpc import GLOBALS

    counter_location = get_counter_location(counter_location)
    if not counter_location.exists() and must_exist:
        raise FileNotFoundError(f"'{_counter_location}' does not exist")
    elif not counter_location.exists() and not must_exist:
        current_iteration = 0
        max_iteration = GLOBALS.N_ITERATIONS
    else:
        with open(counter_location, "r") as f:
            current_iteration = int(next(f))
            try:
                max_iteration = int(next(f))
            except StopIteration:
                max_iteration = GLOBALS.N_ITERATIONS

    return current_iteration, max_iteration


def write_counter(
    current_iteration: Optional[int] = None,
    max_iteration: Optional[int] = None,
    counter_location: Optional[Path] = None,
) -> None:
    """Writes the current and max iteration to the counter file"""
    from ichor.hpc import GLOBALS

    current_iteration = current_iteration or 0
    max_iteration = max_iteration or GLOBALS.N_ITERATIONS
    counter_location = get_counter_location(counter_location)

    if not counter_location.parent.exists():
        mkdir(counter_location.parent)

    with open(counter_location, "w") as f:
        f.write(f"{current_iteration}\n")
        f.write(f"{max_iteration}\n")


def counter_exists(counter_location: Optional[Path] = None) -> bool:
    """Checks whether the counter file exists and whether the current iter is less than the max iter"""
    counter_location = get_counter_location(counter_location)
    if counter_location.exists():
        current_iter, max_iter = read_counter(counter_location)
        if current_iter < max_iter:
            return True
        else:
            remove(counter_location)
    return False


def remove_counter(counter_location: Optional[Path] = None):
    counter_location = get_counter_location(counter_location)
    remove(counter_location)
