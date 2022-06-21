from pathlib import Path
from typing import List, Optional

from ichor.core.analysis.get_atoms import get_atoms_from_path
from ichor.core.analysis.get_input import get_file
from ichor.core.common.io import mkdir
from ichor.core.common.os import input_with_prefill
from ichor.core.files import GJF, WFN, XYZ, PointsDirectory
from ichor.core.menu import Menu, MenuVar
from ichor.hpc import FILE_STRUCTURE, GLOBALS
from ichor.hpc.batch_system import JobID
from ichor.hpc.main.gaussian import submit_gjfs
from ichor.hpc.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                         SubmissionScript)


def _setup_globals():
    global _geometry_file
    if FILE_STRUCTURE["validation_set"].exists():
        _geometry_file = PointsDirectory(FILE_STRUCTURE["validation_set"])[
            0
        ].xyz.path


def _set_geometry_file(geometry_file: MenuVar):
    print("Enter input file location: ")
    geometry_file.var = get_file(Path.cwd(), [XYZ.filetype, GJF.filetype])


# todo: move to hpc
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
    gjf._write_file()

    ichor_command = ICHORCommand(
        func="convert_opt_wfn_to_xyz", func_args=[gjf.path.with_suffix(".wfn")]
    )

    jid = submit_gjfs([gjf.path], script_name=SCRIPT_NAMES["opt"]["gaussian"])
    with SubmissionScript(SCRIPT_NAMES["opt"]["convert"]) as submission_script:
        submission_script.add_command(ichor_command)
    return submission_script.submit(hold=jid)


def _set_keywords(keywords: MenuVar):
    keywords.var = input_with_prefill(
        "Enter keywords: ", prefill=" ".join(keywords.var)
    ).split()


def convert_opt_wfns_to_xyz():
    for f in FILE_STRUCTURE["opt"].iterdir():
        if f.suffix == WFN.filetype:
            convert_opt_wfn_to_xyz(f)


def convert_opt_wfn_to_xyz(wfn_file: Path):
    wfn = WFN(wfn_file)
    xyz = XYZ(wfn_file.parent / f"{wfn_file.stem}_opt{XYZ.filetype}")
    wfn.atoms.to_angstroms()
    xyz.atoms = wfn.atoms
    xyz.write()


def run_gauss_opt_menu():
    geometry_file = MenuVar("Input File", None)
    keywords = MenuVar("Keywords", list(set(GLOBALS.KEYWORDS + ["opt"])))
    with Menu("Geometry Optimisation Menu") as menu:
        menu.add_option(
            "1",
            "Run Geometry Optimisation",
            run_geometry_opt,
            kwargs={"input_file": geometry_file, "keywords": keywords},
        )
        menu.add_option(
            "2", "Convert Optimised WFN to XYZ", convert_opt_wfns_to_xyz
        )
        menu.add_space()
        menu.add_option("i", "Set Input File", _set_geometry_file)
        menu.add_option("k", "Set Keywords", _set_keywords)
        menu.add_space()
        menu.add_var(geometry_file)
        menu.add_var(keywords)
