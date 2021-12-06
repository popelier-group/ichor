from ichor.menu import Menu
from ichor.file_structure import FILE_STRUCTURE
from ichor.files import PointsDirectory, GJF, XYZ
from ichor.analysis.get_path import get_file
from ichor.globals import GLOBALS
from ichor.common.os import input_with_prefill
from typing import Optional,  List
from ichor.analysis.get_atoms import get_atoms_from_path
from ichor.common.io import mkdir
from ichor.main.gaussian import submit_gjfs
from ichor.batch_system import JobID
from ichor.submission_script import SCRIPT_NAMES

from pathlib import Path

_geometry_file = None
_keywords = list(set(GLOBALS.KEYWORDS + ["opt"]))


def _setup_globals():
    global _geometry_file
    if FILE_STRUCTURE["validation_set"].exists():
        _geometry_file = PointsDirectory(FILE_STRUCTURE["validation_set"])[0].xyz.path


def _set_geometry_file():
    global _geometry_file
    print("Enter input file location: ")
    _geometry_file = get_file(Path.cwd(), [XYZ.filetype, GJF.filetype])


def run_geometry_opt(input_file: Path, keywords: Optional[List[str]] = None) -> Optional[JobID]:
    if keywords is None:
        keywords = list(set(GLOBALS.KEYWORDS + ["opt"]))
    atoms = get_atoms_from_path(input_file)

    mkdir(FILE_STRUCTURE["opt"])
    gjf = GJF(FILE_STRUCTURE["opt"] / Path(input_file.name).with_suffix(GJF.filetype))
    gjf.atoms = atoms
    gjf.keywords = keywords
    gjf.write()

    return submit_gjfs([gjf.path], script_name=SCRIPT_NAMES["opt"])


def _set_keywords():
    global _keywords
    _keywords = input_with_prefill("Enter keywords: ", prefill=" ".join(_keywords)).split()


def _gauss_opt_refresh(menu):
    menu.clear_options()
    menu.add_option("1", "Run Geometry Optimisation", run_geometry_opt, kwargs={"input_file": _geometry_file, "keywords": _keywords})
    menu.add_space()
    menu.add_option("i", "Set Input File", _set_geometry_file)
    menu.add_option("k", "Set Keywords", _set_keywords)
    menu.add_space()
    menu.add_message(f"Input File: {_geometry_file}")
    menu.add_message(f"Keywords: {_keywords}")
    menu.add_final_options()


def run_gauss_opt_menu():
    with Menu("Geometry Optimisation Menu", refresh=_gauss_opt_refresh):
        pass
