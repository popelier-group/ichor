"""
Module responsible for locating programs that ichor uses such as:
- ferebus
- tyche
- DLPOLY
"""

from pathlib import Path
from typing import Optional

import ichor
from ichor.ichor_lib.common.io import cp, mkdir, move
from ichor.ichor_lib.common.os import (OTHER_EXECUTE, OTHER_READ, USER_EXECUTE,
                             USER_READ, permissions, set_permission)
from ichor.ichor_hpc.globals import GLOBALS
from ichor.ichor_hpc.machine_setup.machine_setup import MACHINE

_local_bin_directory = Path.home() / ".ichor" / "bin"


class CannotFindProgram(Exception):
    pass


def get_ichor_parent_directory() -> Path:
    return Path(ichor.__file__).parent.resolve()


def machine_bin_directory() -> Path:
    return get_ichor_parent_directory() / "bin" / MACHINE.name


def find_bin(
    name: str, bin_directory: Optional[Path] = None
) -> Optional[Path]:
    if bin_directory is None:
        bin_directory = machine_bin_directory()
    if bin_directory.exists():
        for f in bin_directory.iterdir():
            if f.is_file() and f.name.lower() == name.lower():
                return f


def _copy_bin_to_local(bin_loc: Path) -> Path:
    mkdir(_local_bin_directory)
    new_loc = _local_bin_directory / bin_loc.name
    if (
        not new_loc.exists()
        or open(bin_loc, "rb").read() != open(new_loc, "rb").read()
    ):
        filepart = Path(str(new_loc) + f".{GLOBALS.UID}.filepart")
        if not filepart.exists():
            cp(bin_loc, filepart)
            move(filepart, new_loc)
            set_permission(
                new_loc, USER_READ | USER_EXECUTE | OTHER_READ | OTHER_EXECUTE
            )
    return new_loc


def _get_path_from_globals_or_bin(
    global_name: str, *program_names: str
) -> Path:
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
        raise CannotFindProgram(
            f"Cannot find program '{program_name}'. Add program to {machine_bin_directory().absolute()} or set '{global_name}' in the config file"
        )

    read_ok, _, execute_ok = permissions(bin_loc)
    if not (read_ok and execute_ok):
        bin_loc = _copy_bin_to_local(bin_loc)
    return bin_loc


def get_ferebus_path() -> Path:
    return _get_path_from_globals_or_bin("FEREBUS_LOCATION", "ferebus")


def get_dlpoly_path() -> Path:
    return _get_path_from_globals_or_bin(
        "DLPOLY_LOCATION", "dlpoly", "dlpoly.z"
    )


def get_tyche_path() -> Path:
    return _get_path_from_globals_or_bin("TYCHE_LOCATION", "tyche")
