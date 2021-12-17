from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from ichor.analysis.geometry.geometry_calculator import (
    calculate_angles, calculate_bonds, calculate_dihedrals,
    internal_feature_names)
from ichor.analysis.get_atoms import get_atoms_from_path
from ichor.analysis.get_path import get_path
from ichor.batch_system import JobID
from ichor.file_structure import FILE_STRUCTURE
from ichor.files import PointsDirectory, Trajectory
from ichor.menu import Menu
from ichor.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                     SubmissionScript)
from ichor.units import Angle, degrees_to_radians

_input_location = None
_output_location = Path("geometry.xlsx")

_submit = False

_calc_bonds = True
_calc_angles = True
_calc_dihedrals = True
_calc_modified_dihedrals = True

_angle_units = Angle.Degrees


def _write_to_excel(writer, sheet_name, data, create_summary=False):
    import pandas as pd

    if len(data) > 0:
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name=sheet_name)

        if create_summary:
            summary = {
                heading: {
                    "min": np.min(values),
                    "avg": np.mean(values),
                    "max": np.max(values),
                }
                for heading, values in data.items()
            }
            summary_df = pd.DataFrame(summary).reindex(
                index=["min", "avg", "max"]
            )
            summary_df.to_excel(writer, sheet_name=f"{sheet_name}_Summary")


def geometry_analysis(input_location: Path, output_location: Path):
    if input_location.suffix == Trajectory.filetype:
        points = Trajectory(input_location)
    elif PointsDirectory.check_path(input_location):
        points = [p.atoms for p in PointsDirectory(input_location)]
    else:
        points = [get_atoms_from_path(input_location)]

    bonds = []
    angles = []
    dihedrals = []
    modified_dihedrals = []
    for point in points:
        if _calc_bonds:
            bonds.append(calculate_bonds(point))
        if _calc_angles:
            angles.append(calculate_angles(point))
        if _calc_dihedrals:
            dihedrals.append(calculate_dihedrals(point))
        if _calc_modified_dihedrals:
            dihedral = (
                calculate_dihedrals(point)
                if not _calc_dihedrals
                else dihedrals[-1]
            )
            if not modified_dihedrals:
                modified_dihedrals.append(dihedral)
            else:
                diff = (dihedral - modified_dihedrals[-1] + 180) % 360 - 180
                modified_dihedrals.append(modified_dihedrals[-1] + diff)

    bonds = np.array(bonds)
    angles = np.array(angles)
    dihedrals = np.array(dihedrals)
    modified_dihedrals = np.array(modified_dihedrals)

    if _angle_units is Angle.Radians:
        angles = degrees_to_radians(angles)
        dihedrals = degrees_to_radians(dihedrals)
        modified_dihedrals = degrees_to_radians(modified_dihedrals)

    bond_headings, angle_headings, dihedral_headings = internal_feature_names(
        points[-1]
    )
    bonds = {
        bond_heading: bond
        for bond_heading, bond in zip(bond_headings, bonds.T)
    }
    angles = {
        angle_heading: angle
        for angle_heading, angle in zip(angle_headings, angles.T)
    }
    dihedrals = {
        dihedral_heading: dihedral
        for dihedral_heading, dihedral in zip(dihedral_headings, dihedrals.T)
    }
    modified_dihedrals = {
        dihedral_heading: modified_dihedral
        for dihedral_heading, modified_dihedral in zip(
            dihedral_headings, modified_dihedrals.T
        )
    }

    with pd.ExcelWriter(output_location) as writer:
        if len(bonds) > 1:
            _write_to_excel(writer, "Bonds", bonds, create_summary=True)
        if len(angles) > 1:
            _write_to_excel(writer, "Angles", angles, create_summary=True)
        if len(dihedrals) > 1:
            _write_to_excel(writer, "Dihedrals", dihedrals)
        if len(modified_dihedrals) > 1:
            _write_to_excel(writer, "Modified Dihedrals", modified_dihedrals)


def submit_geometry_analysis(
    input_location: Path, output_location: Path
) -> JobID:
    with SubmissionScript(
        SCRIPT_NAMES["analysis"]["geometry"]
    ) as submission_script:
        submission_script.add_command(
            ICHORCommand(
                func="geometry_analysis",
                func_args=[input_location, output_location],
            )
        )
    return submission_script.submit()


def run_geometry_analysis(
    input_location: Path, output_location: Path
) -> Optional[JobID]:
    if _submit:
        return submit_geometry_analysis(input_location, output_location)
    else:
        run_geometry_analysis(input_location, output_location)


def _toggle_calc_bonds():
    global _calc_bonds
    _calc_bonds = not _calc_bonds


def _toggle_calc_angles():
    global _calc_angles
    _calc_angles = not _calc_angles


def _toggle_calc_calc_dihedrals():
    global _calc_dihedrals
    _calc_dihedrals = not _calc_dihedrals


def _toggle_calc_modified_dihedrals():
    global _calc_modified_dihedrals
    _calc_modified_dihedrals = not _calc_modified_dihedrals


def _set_input():
    global _input_location
    _input_location = get_path(
        prompt="Enter Input Location", prefill=_input_location
    )


def _set_output():
    global _output_location
    _output_location = get_path(
        prompt="Enter Output Location", prefill=_output_location
    )


def _toggle_submit():
    global _submit
    _submit = not _submit


def _toggle_angle_units():
    global _angle_units
    _angle_units = (
        Angle.Radians if _angle_units is Angle.Degrees else Angle.Degrees
    )


def _geometry_analysis_menu_refresh(menu):
    menu.clear_options()
    menu.add_option("1", "Run Geometry Analysis", run_geometry_analysis)
    menu.add_space()
    menu.add_option("i", "Set Input", _set_input)
    menu.add_option("o", "Set Output", _set_output)
    menu.add_option("submit", "Toggle Submit Analysis", _toggle_submit)
    menu.add_space()
    menu.add_option("b", "Toggle Calculate Bonds", _toggle_calc_bonds)
    menu.add_option("a", "Toggle Calculate Angles", _toggle_calc_angles)
    menu.add_option(
        "d", "Toggle Calculate Dihedrals", _toggle_calc_calc_dihedrals
    )
    menu.add_option(
        "m",
        "Toggle Calculate Modified Dihedrals",
        _toggle_calc_modified_dihedrals,
    )
    menu.add_space()
    menu.add_option(
        "u", "Toggle Angle Units", _toggle_angle_units, _toggle_angle_units
    )
    menu.add_space()
    menu.add_message(f"Input Location: {_input_location}")
    menu.add_message(f"Output Location: {_output_location}")
    menu.add_message(f"Submit Analysis: {_submit}")
    menu.add_space()
    menu.add_message(f"Calculate Bonds: {_calc_bonds}")
    menu.add_message(f"Calculate Angles: {_calc_angles}")
    menu.add_message(f"Calculate Dihedrals: {_calc_dihedrals}")
    menu.add_message(
        f"Calculate Modified Dihedrals: {_calc_modified_dihedrals}"
    )
    menu.add_space()
    menu.add_option(f"Angle Units: {_angle_units.name}")
    menu.add_final_options()


def geometry_analysis_menu():
    global _input_location
    _input_location = FILE_STRUCTURE["training_set"]
    with Menu(
        "Geometry Analysis Menu", refresh=_geometry_analysis_menu_refresh
    ):
        pass
