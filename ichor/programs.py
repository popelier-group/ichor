"""
Module responsible for locating programs that ichor uses such as:
- ferebus
- tyche
- DLPOLY
"""

from ichor.globals import GLOBALS
from ichor.machine import MACHINE
import ichor

from pathlib import Path
from typing import Optional


class CannotFindProgram(Exception):
    pass


def get_ichor_parent_directory() -> Path:
    return Path(ichor.__file__).parent.resolve()


def machine_bin_directory() -> Path:
    return get_ichor_parent_directory() / "bin" / MACHINE.name


def find_bin(name: str) -> Optional[Path]:
    machine_bin = machine_bin_directory()
    if machine_bin.exists():
        for f in machine_bin.iterdir():
            if f.is_file() and f.name.lower() == name.lower():
                return f


def _get_path_from_globals_or_bin(global_name: str, *program_names: str) -> Path:
    global_loc = GLOBALS.get(global_name)
    if global_loc is not None and global_loc.exists():
        return global_loc

    bin_loc = None
    for program_name in program_names:
        bin_loc = find_bin(program_name)
        if bin_loc is not None:
            break
    if bin_loc is None:
        program_name = "|".join(program_names)
        raise CannotFindProgram(f"Cannot find program '{program_name}'. Add program to {machine_bin_directory().absolute()} or set '{global_name}' in the config file")
    return bin_loc


def get_ferebus_path() -> Path:
    return _get_path_from_globals_or_bin("FEREBUS_LOCATION", "ferebus")


def get_dlpoly_path() -> Path:
    return _get_path_from_globals_or_bin("DLPOLY_LOCATION", "dlpoly", "dlpoly.z")


def get_tyche_path() -> Path:
    return _get_path_from_globals_or_bin("TYCHE_LOCATION", "tyche")
