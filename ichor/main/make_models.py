from enum import Enum
from pathlib import Path
from typing import List, Optional

import numpy as np

from ichor import constants
from ichor.batch_system import JobID
from ichor.common.io import cp, mkdir
from ichor.common.str import get_digits
from ichor.menu import Menu
from ichor.points import PointsDirectory
from ichor.submission_script import (SCRIPT_NAMES, FerebusCommand,
                                     SubmissionScript)
from ichor.tab_completer import ListCompleter

model_data_location: Path = Path()
_model_data: Optional[PointsDirectory] = None
n_training_points: int = 0
atom_models: List[str] = []


class ModelType(Enum):
    iqa = "iqa"
    q00 = "q00"
    q10 = "q10"
    q11c = "q11c"
    q11s = "q11s"
    q20 = "q20"
    q21c = "q21c"
    q21s = "q21s"
    q22c = "q22c"
    q22s = "q22s"
    q30 = "q30"
    q31c = "q31c"
    q31s = "q31s"
    q32c = "q32c"
    q32s = "q32s"
    q33c = "q33c"
    q33s = "q33s"
    q40 = "q40"
    q41c = "q41c"
    q41s = "q41s"
    q42c = "q42c"
    q42s = "q42s"
    q43c = "q43c"
    q43s = "q43s"
    q44c = "q44c"
    q44s = "q44s"

    @classmethod
    def to_str(cls, ty: "ModelType"):
        return ty.value


model_types: List[ModelType] = [ModelType.iqa]
atoms: List[str] = []


def setup(directory: Path):
    global model_data_location
    global _model_data
    global n_training_points
    global atoms
    global atom_models

    model_data_location = directory
    _model_data = PointsDirectory(directory)
    n_training_points = len(_model_data)
    atoms = [atom.name for atom in _model_data[0].atoms]
    atom_models = list(atoms)


def toggle_model_type(ty: ModelType):
    global model_types
    if ty in model_types:
        del model_types[model_types.index(ty)]
    else:
        model_types += [ty]


def select_model_type():
    global model_types
    while True:
        Menu.clear_screen()
        print("Select Models To Create")
        model_type_list = list(map(ModelType.to_str, ModelType)) + [
            "multipoles"
        ]
        with ListCompleter(model_type_list):
            for ty in ModelType:
                print(
                    f"[{'x' if ty in model_types else ' '}] {ModelType.to_str(ty)}"
                )
            print()
            ans = input(">> ")
            ans = ans.strip().lower()
            if ans == "":
                return
            elif ans in model_type_list:
                if ans == "multipoles":
                    for multipole in constants.multipole_names:
                        if multipole in model_type_list:
                            toggle_model_type(ModelType[multipole])
                else:
                    toggle_model_type(ModelType[ans])
            elif ans in ["c", "clear"]:
                model_types.clear()


def select_number_of_training_points():
    global n_training_points
    print(f"Input Number of Training Points (1-{len(_model_data)})")
    while True:
        ans = input(">> ")
        try:
            ans = int(ans)
            if not 1 <= ans <= len(_model_data):
                print(
                    f"Error: Answer must be between 1 and {len(_model_data)}"
                )
            else:
                n_training_points = ans
                break
        except TypeError:
            print("Error: Answer must be an integer")


def toggle_atom_model(atom: str):
    global atom_models
    if atom in atom_models:
        del atom_models[atom_models.index(atom)]
    else:
        atom_models += [atom]


def select_atoms():
    global atom_models
    with ListCompleter(atoms):
        while True:
            print("Select Atoms To Create Models For")
            for atom in atoms:
                print(f"[{'x'if atom in atom_models else ' '}] {atom}")
            print()
            ans = input(">> ")
            ans = ans.strip()
            if ans == "":
                return
            elif ans in atoms:
                toggle_atom_model(ans)
            elif ans in ["c", "clear"]:
                atom_models.clear()


def make_models_menu_refresh(menu):
    menu.clear_options()
    menu.add_option("1", "Make Models", _make_models)
    menu.add_space()
    menu.add_option("t", "Select Model Type", select_model_type)
    menu.add_option(
        "n",
        "Select Number of Training Points",
        select_number_of_training_points,
    )
    menu.add_option("a", "Select Atoms", select_atoms)
    menu.add_space()
    menu.add_message(
        f"Model Type(s): {', '.join(map(ModelType.to_str, model_types))}"
    )
    menu.add_message(f"Number of Training Points: {n_training_points}")
    menu.add_message(f"Atoms: {', '.join(map(str, atom_models))}")
    menu.add_final_options()


def make_models_menu(directory: Path):
    setup(directory)
    with Menu("Make Models Menu", refresh=make_models_menu_refresh) as menu:
        pass


def make_models(
    directory: Path,
    atoms: Optional[List[str]] = None,
    ntrain: Optional[int] = None,
    types: Optional[List[str]] = None,
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    global model_data_location
    global _model_data
    global n_training_points
    global atom_models
    global model_types

    model_data_location = directory
    _model_data = PointsDirectory(directory)

    n_training_points = ntrain or len(_model_data)
    model_types = types or [ModelType.iqa]
    atom_models = atoms or [atom.atom_num for atom in _model_data[0].atoms]

    return _make_models(hold=hold)


def move_models(model_dir: Optional[Path] = None):
    from ichor.globals import GLOBALS

    mkdir(GLOBALS.FILE_STRUCTURE["models"])

    if model_dir is None:
        model_dir = GLOBALS.FILE_STRUCTURE["ferebus"]

    for d in model_dir.iterdir():
        if d.is_dir() and d != GLOBALS.FILE_STRUCTURE["models"]:
            for f in d.iterdir():
                if f.suffix == ".model":
                    cp(f, GLOBALS.FILE_STRUCTURE["models"])
        elif d.is_file() and d.suffix == ".model":
            cp(d, GLOBALS.FILE_STRUCTURE["models"])


def _make_models(hold: Optional[JobID] = None) -> Optional[JobID]:
    ferebus_directories = []

    for atom in atom_models:
        training_data = []
        features = _model_data[atom].features
        for i, point in enumerate(_model_data):
            properties = {
                ty.value: getattr(point, ty.value)[atom] for ty in model_types
            }
            training_data += [(features[i], properties)]

        ferebus_directory = write_training_set(atom, training_data)
        ferebus_directories += [ferebus_directory]

    return make_ferebus_scrpt(ferebus_directories, hold=hold)


def make_ferebus_scrpt(
    ferebus_directories: List[Path], hold: Optional[JobID] = None
) -> Optional[JobID]:
    script_name = SCRIPT_NAMES["ferebus"]
    ferebus_script = SubmissionScript(script_name)
    for ferebus_directory in ferebus_directories:
        ferebus_script.add_command(FerebusCommand(ferebus_directory))
    ferebus_script.write()
    return ferebus_script.submit(hold=hold)


def write_training_set(atom, training_data) -> Path:
    from ichor.globals import GLOBALS

    ferebus_directory = GLOBALS.FILE_STRUCTURE["ferebus"] / atom
    mkdir(ferebus_directory, empty=True)

    ntrain = len(training_data)

    training_set_file = (
        ferebus_directory / f"{GLOBALS.SYSTEM_NAME}_{atom}_TRAINING_SET.csv"
    )
    write_ftoml(ferebus_directory, atom)
    with open(training_set_file, "w") as ts:
        if ntrain > 0:
            inputs, outputs = training_data[0]
            input_headers = [f"f{i+1}" for i in range(len(inputs))]
            output_headers = [f"{output}" for output in outputs.keys()]
            ts.write(
                f",{','.join(input_headers)},{','.join(output_headers)}\n"
            )
            for i, (inputs, outputs) in enumerate(training_data):
                ts.write(
                    f"{i},{','.join(map(str, inputs))},{','.join(map(str, outputs.values()))}\n"
                )

    return ferebus_directory


def write_ftoml(ferebus_directory, atom):
    from ichor.atoms.calculators.feature_calculator.alf_feature_calculator import \
        ALFFeatureCalculator
    from ichor.globals import GLOBALS

    ftoml_file = ferebus_directory / "ferebus.toml"
    alf = list(np.array(ALFFeatureCalculator._alf[get_digits(atom) - 1]) + 1)

    with open(ftoml_file, "w") as ftoml:
        ftoml.write("[system]\n")
        ftoml.write(f'name = "{GLOBALS.SYSTEM_NAME}"\n')
        ftoml.write(f"natoms = {len(GLOBALS.ATOMS)}\n")
        ftoml.write(f"atoms = [\n")
        ftoml.write(
            f'  {{name="{atom}", alf=[{alf[0]}, {alf[1]}, {alf[2]}]}}\n'
        )
        ftoml.write("]\n")
        ftoml.write("\n")
        ftoml.write("[model]\n")
        ftoml.write(f'mean = "{GLOBALS.FEREBUS_MEAN}"\n')
        ftoml.write(f'optimiser = "{GLOBALS.FEREBUS_OPTIMISATION}"\n')
        ftoml.write(f'kernel = "k1"\n')
        if GLOBALS.STANDARDISE:
            ftoml.write(f"standardise = true\n")
        ftoml.write("\n")
        ftoml.write("[optimiser]\n")
        ftoml.write(f"search_min = {GLOBALS.FEREBUS_THETA_MIN}\n")
        ftoml.write(f"search_max = {GLOBALS.FEREBUS_THETA_MAX}\n")
        ftoml.write("\n")
        ftoml.write("[optimiser.pso]\n")
        ftoml.write(f"swarm_size = {GLOBALS.FEREBUS_SWARM_SIZE}\n")
        ftoml.write(f"iterations = {GLOBALS.FEREBUS_MAX_ITERATION}\n")
        ftoml.write(f"inertia_weight = {GLOBALS.FEREBUS_INERTIA_WEIGHT}\n")
        ftoml.write(
            f"cognitive_learning_rate = {GLOBALS.FEREBUS_COGNITIVE_LEARNING_RATE}\n"
        )
        ftoml.write(
            f"social_learning_rate = {GLOBALS.FEREBUS_SOCIAL_LEARNING_RATE}\n"
        )
        ftoml.write(f'stopping_criteria="relative_change"\n')
        ftoml.write("\n")
        ftoml.write(f"[optimiser.pso.relative_change]\n")
        ftoml.write(f"tolerance={GLOBALS.FEREBUS_TOLERANCE}\n")
        ftoml.write(f"stall_iterations={GLOBALS.FEREBUS_STALL_ITERATIONS}\n")
        ftoml.write("\n")
        ftoml.write("[kernels.k1]\n")
        ftoml.write(f'type = "{GLOBALS.KERNEL}"\n')
