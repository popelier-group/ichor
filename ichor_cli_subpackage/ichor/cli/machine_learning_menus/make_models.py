from pathlib import Path

from ichor.core.files import PointsDirectory
from ichor.core.menu import (
    Menu,
    MenuVar,
    select_multiple_from_list,
    toggle_bool_var,
)
from ichor.hpc import GLOBALS
from ichor.hpc.programs.qct import (
    QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM,
    QuantumChemicalTopologyProgram,
)
from ichor.hpc.main.make_models import (
    default_model_type,
    create_ferebus_directories_and_submit,
    MODEL_TYPES,
)


def select_number_of_training_points(
    n_training_points: MenuVar[int], model_data: MenuVar[PointsDirectory]
):
    max_training_points = len(model_data.var)
    print(f"Input Number of Training Points (1-{max_training_points})")
    while True:
        ans = input(">> ")
        try:
            ans = int(ans)
            if not 1 <= ans <= max_training_points:
                print(
                    f"Error: Answer must be between 1 and {max_training_points}"
                )
            else:
                n_training_points.var = ans
                break
        except TypeError:
            print("Error: Answer must be an integer")


def make_models_menu(directory: Path):
    """The handler function for making models from a specific directory. To make the models, both Gaussian and AIMALL have to be ran
    for the points that are in the directory."""

    model_data = MenuVar("Model Data", PointsDirectory(directory))
    n_training_points = MenuVar(
        "Number of Training Points", len(model_data.var)
    )
    atom_names = [atom.name for atom in model_data.var[0].atoms]
    selected_atoms = MenuVar("Atoms", list(atom_names))

    model_types = MenuVar("Model Types", [default_model_type])

    add_dispersion_to_iqa = MenuVar(
        "Add Dispersion to IQA", GLOBALS.ADD_DISPERSION_TO_IQA
    )

    with Menu("Make Models Menu") as menu:
        menu.add_option(
            "1",
            "Make Models",
            create_ferebus_directories_and_submit,
            args=[model_data, atom_names, model_types],
        )
        menu.add_space()
        menu.add_option(
            "t",
            "Select Model Type",
            select_multiple_from_list,
            args=[
                MODEL_TYPES(),
                model_types,
                "Select Models To Create",
            ],
        )
        menu.add_option(
            "n",
            "Select Number of Training Points",
            select_number_of_training_points,
            args=[n_training_points, model_data],
        )
        menu.add_option(
            "a",
            "Select Atoms",
            select_multiple_from_list,
            args=[
                atom_names,
                selected_atoms,
                "Select Atoms To Create Models For",
            ],
        )
        if (
            QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM()
            is QuantumChemicalTopologyProgram.Morfi
        ):
            menu.add_option(
                "d",
                "Toggle Add Dispersion to IQA",
                toggle_bool_var,
                args=[add_dispersion_to_iqa],
            )
        menu.add_space()
        menu.add_var(model_types)
        menu.add_var(n_training_points)
        menu.add_var(selected_atoms)
        if (
            QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM()
            is QuantumChemicalTopologyProgram.Morfi
        ):
            menu.add_var(add_dispersion_to_iqa)
