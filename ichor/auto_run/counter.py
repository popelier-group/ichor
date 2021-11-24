from pathlib import Path
from typing import Optional, Tuple

from ichor.common.io import mkdir
from ichor.file_structure import FILE_STRUCTURE

_counter_location = FILE_STRUCTURE["counter"]


def _get_counter_location(counter_location: Optional[Path] = None) -> Path:
    counter_location = counter_location or _counter_location

    if counter_location.is_dir():
        counter_location = counter_location / _counter_location

    return counter_location


def read_counter(
    counter_location: Optional[Path] = None, must_exist: bool = True
) -> Tuple[int, int]:
    """Reads the counter file, returns current iteration and max iteration"""
    from ichor.globals import GLOBALS

    counter_location = _get_counter_location(counter_location)
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
    from ichor.globals import GLOBALS

    current_iteration = current_iteration or 0
    max_iteration = max_iteration or GLOBALS.N_ITERATIONS
    counter_location = _get_counter_location(counter_location)

    if not counter_location.parent.exists():
        mkdir(counter_location.parent)

    with open(counter_location, "w") as f:
        f.write(f"{current_iteration}\n")
        f.write(f"{max_iteration}\n")
