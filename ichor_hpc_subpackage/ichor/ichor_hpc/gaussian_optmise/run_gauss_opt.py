from pathlib import Path
from typing import List, Optional

from ichor.ichor_lib.analysis.get_atoms import get_atoms_from_path
from ichor.ichor_lib.analysis.get_path import get_file
from ichor.batch_system import JobID
from ichor.ichor_lib.common.io import mkdir
from ichor.ichor_lib.common.os import input_with_prefill
from ichor_hpc.file_structure.file_structure import FILE_STRUCTURE
from ichor.ichor_lib.files import GJF, WFN, XYZ, PointsDirectory
from ichor.globals import GLOBALS
from ichor.main.gaussian import submit_gjfs
from ichor.menus.menu import Menu
from ichor.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                     SubmissionScript)

_geometry_file = None
_keywords = list(set(GLOBALS.KEYWORDS + ["opt"]))


def _setup_globals():
    global _geometry_file
    if FILE_STRUCTURE["validation_set"].exists():
        _geometry_file = PointsDirectory(FILE_STRUCTURE["validation_set"])[
            0
        ].xyz.path


def _set_geometry_file():
    global _geometry_file
    print("Enter input file location: ")
    _geometry_file = get_file(Path.cwd(), [XYZ.filetype, GJF.filetype])


def run_geometry_opt(
    input_file: Path, keywords: Optional[List[str]] = None
) -> Optional[JobID]:
    if keywords is None:
        keywords = list(set(GLOBALS.KEYWORDS + ["opt"]))
    atoms = get_atoms_from_path(input_file)

    mkdir(FILE_STRUCTURE["opt"])
    gjf = GJF(
        FILE_STRUCTURE["opt"] / Path(input_file.name).with_suffix(GJF.filetype)
    )
    gjf.atoms = atoms
    gjf.keywords = keywords
    gjf.write()

    ichor_command = ICHORCommand(
        func="convert_opt_wfn_to_xyz", func_args=[gjf.path.with_suffix(".wfn")]
    )

    jid = submit_gjfs([gjf.path], script_name=SCRIPT_NAMES["opt"]["gaussian"])
    with SubmissionScript(SCRIPT_NAMES["opt"]["convert"]) as submission_script:
        submission_script.add_command(ichor_command)
    return submission_script.submit(hold=jid)


def _set_keywords():
    global _keywords
    _keywords = input_with_prefill(
        "Enter keywords: ", prefill=" ".join(_keywords)
    ).split()


def _gauss_opt_refresh(menu):
    menu.clear_options()
    menu.add_option(
        "1",
        "Run Geometry Optimisation",
        run_geometry_opt,
        kwargs={"input_file": _geometry_file, "keywords": _keywords},
    )
    menu.add_option(
        "2", "Convert Optimised WFN to XYZ", convert_opt_wfns_to_xyz
    )
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


def convert_opt_wfns_to_xyz():
    for f in FILE_STRUCTURE["opt"].iterdir():
        if f.suffix == WFN.filetype:
            convert_opt_wfn_to_xyz(f)


def convert_opt_wfn_to_xyz(wfn_file: Path):
    wfn = WFN(wfn_file)
    xyz = XYZ(wfn_file.parent / (wfn_file.stem + "_opt" + XYZ.filetype))
    wfn.atoms.to_angstroms()
    xyz.atoms = wfn.atoms
    xyz.write()
