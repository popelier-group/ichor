from pathlib import Path

from ichor.core.analysis.get_path import get_generic_path
from ichor.core.analysis.s_curves.compact_s_curves import \
    calculate_compact_s_curves
from ichor.core.analysis.s_curves.s_curves import calculate_s_curves
from ichor.core.menu import Menu, MenuVar, choose_dir_var


def choose_output_location(output_location: MenuVar[Path]):
    output_location.var = get_generic_path(
        prompt="Enter s-curves output: ", prefill=str(output_location.var)
    )
    if output_location.var.suffix not in [".xlsx", ".xls"]:
        output_location.var = output_location.var.with_suffix(".xlsx")


def s_curve_menu():
    from ichor.hpc import FILE_STRUCTURE

    validation_set_location = MenuVar(
        "Validation Set Location", FILE_STRUCTURE["validation_set"]
    )
    model_location = MenuVar("Model Location", FILE_STRUCTURE["models"])
    output_location = MenuVar("Output Location", Path("s-curves.xlsx"))

    with Menu("S-Curve Analysis Menu") as menu:
        menu.add_option(
            "1",
            "Calculate Compact S-Curves",
            calculate_compact_s_curves,
            kwargs={
                "model_location": model_location,
                "validation_set_location": validation_set_location,
                "output_location": output_location,
            },
        )
        menu.add_option(
            "2",
            "Calculate S-Curves",
            calculate_s_curves,
            kwargs={
                "model_location": model_location,
                "validation_set_location": validation_set_location,
                "output_location": output_location,
            },
        )

        menu.add_space()
        menu.add_option(
            "vs",
            "Choose Validation Set",
            choose_dir_var,
            args=[validation_set_location, "Enter Validation Set Location: "],
        )
        menu.add_option(
            "model",
            "Choose Model",
            choose_dir_var,
            args=[model_location, "Enter Model Directory: "],
        )
        menu.add_option(
            "output", "Choose Output Location", choose_output_location
        )
        menu.add_space()
        menu.add_var(validation_set_location)
        menu.add_var(model_location)
        menu.add_var(output_location)
