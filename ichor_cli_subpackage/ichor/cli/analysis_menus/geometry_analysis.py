from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from ichor.core.analysis.geometry.geometry_calculator import (
    calculate_angles, calculate_bonds, calculate_dihedrals,
    internal_feature_names)
from ichor.core.analysis.get_atoms import get_atoms_from_path
from ichor.core.files import PointsDirectory, Trajectory
from ichor.core.menu import Menu, MenuVar, set_path_var, toggle_bool_var
from ichor.core.units import Angle, degrees_to_radians
from ichor.hpc import FILE_STRUCTURE
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                         SubmissionScript)

# todo: move to hpc


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


def geometry_analysis(
    input_location: Path,
    output_location: Path,
    calc_bonds: bool = True,
    calc_angles: bool = True,
    calc_dihedrals: bool = True,
    calc_modified_dihedrals: bool = True,
    angle_units: Angle = Angle.Degrees,
):
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
        if calc_bonds:
            bonds.append(calculate_bonds(point))
        if calc_angles:
            angles.append(calculate_angles(point))
        if calc_dihedrals:
            dihedrals.append(calculate_dihedrals(point))
        if calc_modified_dihedrals:
            dihedral = (
                calculate_dihedrals(point)
                if not calc_dihedrals
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

    if angle_units is Angle.Radians:
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
    input_location: Path,
    output_location: Path,
    calc_bonds: bool = True,
    calc_angles: bool = True,
    calc_dihedrals: bool = True,
    calc_modified_dihedrals: bool = True,
    angle_units: Angle = Angle.Degrees,
) -> JobID:
    with SubmissionScript(
        SCRIPT_NAMES["analysis"]["geometry"]
    ) as submission_script:
        submission_script.add_command(
            ICHORCommand(
                func="geometry_analysis",
                func_args=list(
                    map(
                        str,
                        [
                            input_location,
                            output_location,
                            calc_bonds,
                            calc_angles,
                            calc_dihedrals,
                            calc_modified_dihedrals,
                            angle_units,
                        ],
                    )
                ),
            )
        )
    return submission_script.submit()


def run_geometry_analysis(
    input_location: Path,
    output_location: Path,
    calc_bonds: bool = True,
    calc_angles: bool = True,
    calc_dihedrals: bool = True,
    calc_modified_dihedrals: bool = True,
    angle_units: Angle = Angle.Degrees,
    submit: bool = False,
) -> Optional[JobID]:
    if submit:
        return submit_geometry_analysis(
            input_location,
            output_location,
            calc_bonds,
            calc_angles,
            calc_dihedrals,
            calc_modified_dihedrals,
            angle_units,
        )
    else:
        geometry_analysis(
            input_location,
            output_location,
            calc_bonds,
            calc_angles,
            calc_dihedrals,
            calc_modified_dihedrals,
            angle_units,
        )


def _toggle_angle_units(angle_units: MenuVar[Angle]):
    angle_units.var = (
        Angle.Radians if angle_units.var is Angle.Degrees else Angle.Degrees
    )


def _geometry_analysis_menu_refresh(menu):
    menu.clear_options()
    menu.add_final_options()


def geometry_analysis_menu():
    input_location = MenuVar("Input Location", FILE_STRUCTURE["training_set"])
    output_location = MenuVar("Output Location", Path("geometry.xlsx"))

    submit = MenuVar("Submit Analysis", False)

    calc_bonds = MenuVar("Calculate Bonds", True)
    calc_angles = MenuVar("Calculate Angles", True)
    calc_dihedrals = MenuVar("Calculate Dihedrals", True)
    calc_modified_dihedrals = MenuVar("Calculate Modified Dihedrals", True)

    angle_units = MenuVar("Angle Units", Angle.Degrees)

    with Menu("Geometry Analysis Menu") as menu:
        menu.add_option(
            "1",
            "Run Geometry Analysis",
            run_geometry_analysis,
            args=[
                input_location,
                output_location,
                calc_bonds,
                calc_angles,
                calc_dihedrals,
                calc_modified_dihedrals,
                angle_units,
                submit,
            ],
        )
        menu.add_space()
        menu.add_option(
            "i",
            "Set Input",
            set_path_var,
            args=[input_location, "Set Input Location"],
        )
        menu.add_option(
            "o",
            "Set Output",
            set_path_var,
            args=[output_location, "Set Output Location"],
        )
        menu.add_option(
            "submit", "Toggle Submit Analysis", toggle_bool_var, args=[submit]
        )
        menu.add_space()
        menu.add_option(
            "b", "Toggle Calculate Bonds", toggle_bool_var, args=[calc_bonds]
        )
        menu.add_option(
            "a", "Toggle Calculate Angles", toggle_bool_var, args=[calc_angles]
        )
        menu.add_option(
            "d",
            "Toggle Calculate Dihedrals",
            toggle_bool_var,
            args=[calc_dihedrals],
        )
        menu.add_option(
            "m",
            "Toggle Calculate Modified Dihedrals",
            toggle_bool_var,
            args=[calc_modified_dihedrals],
        )
        menu.add_space()
        menu.add_option(
            "u", "Toggle Angle Units", _toggle_angle_units, args=[angle_units]
        )
        menu.add_space()
        menu.add_var(input_location)
        menu.add_var(output_location)
        menu.add_var(submit)
        menu.add_space()
        menu.add_var(calc_bonds)
        menu.add_var(calc_angles)
        menu.add_var(calc_dihedrals)
        menu.add_var(calc_modified_dihedrals)
        menu.add_space()
        menu.add_var(angle_units)
