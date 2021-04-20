from pathlib import Path
from ichor.points import PointsDirectory
from ichor.menu import Menu
from ichor.tab_completer import ListCompleter
from ichor.common.io import mkdir

from enum import Enum
from ichor import constants
from typing import List, Optional

from ichor.debugging import printq


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
    def to_str(cls, ty: 'ModelType'):
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
    atoms = [atom.atom_num for atom in _model_data[0].atoms]
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
        model_type_list = list(map(ModelType.to_str, ModelType)) + ["multipoles"]
        with ListCompleter(model_type_list):
            for ty in ModelType:
                print(f"[{'x' if ty in model_types else ' '}] {ModelType.to_str(ty)}")
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
                print(f"Error: Answer must be between 1 and {len(_model_data)}")
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
    menu.add_option("n", "Select Number of Training Points", select_number_of_training_points)
    menu.add_option("a", "Select Atoms", select_atoms)
    menu.add_space()
    menu.add_message(f"Model Type(s): {', '.join(map(ModelType.to_str, model_types))}")
    menu.add_message(f"Number of Training Points: {n_training_points}")
    menu.add_message(f"Atoms: {', '.join(atom_models)}")
    menu.add_final_options()


def make_models_menu(directory: Path):
    setup(directory)
    with Menu("Make Models Menu", refresh=make_models_menu_refresh) as menu:
        pass


def make_models(directory: Path, atoms: Optional[List[str]] = None, ntrain: Optional[int] = None, types: Optional[List[str]] = None):
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

    _make_models()


def _make_models():
    from ichor.globals import GLOBALS

    ferebus_directories = []

    for atom in atom_models:
        ferebus_directory = GLOBALS.FILE_STRUCTURE["ferebus"] / atom
        mkdir(ferebus_directory, empty=True)
        training_data = []
        for point in _model_data:
            # features = point.features[atom]
            features = point.features[point.atoms.i(atom)]
            properties = {ty.value: getattr(point, ty.value)[atom] for ty in model_types}
            training_data += [(features, properties)]

        print(training_data)
        quit()
        write_training_set(training_data, ferebus_directory)
        ferebus_directories += [ferebus_directory]


