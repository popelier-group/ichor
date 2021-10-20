from enum import Enum
from pathlib import Path
from typing import List, Optional

import numpy as np

from ichor import constants
from ichor.batch_system import JobID
from ichor.common.io import cp, mkdir
from ichor.common.str import get_digits
from ichor.files import PointsDirectory
from ichor.logging import logger
from ichor.menu import Menu
from ichor.qct import (QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM,
                       QuantumChemicalTopologyProgram)
from ichor.submission_script import (SCRIPT_NAMES, FerebusCommand,
                                     SubmissionScript)
from ichor.tab_completer import ListCompleter

model_data_location: Path = Path()
_model_data: Optional[PointsDirectory] = None
n_training_points: int = 0
atom_models_to_make: List[str] = []

atoms_selected = False
models_selected = False


# todo: refactor to use ichor.common.types.enum.Enum
class ModelType(Enum):
    """Enum used for all the different models we make: iqa and multipole moments."""

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
    iqa_dispersion = "iqa+dispersion"
    dispersion = "dispersion"

    @classmethod
    def to_str(cls, ty: "ModelType"):
        """Convert the named element to its string value."""
        return ty.value

    @classmethod
    def from_str(cls, ty: str) -> "ModelType":
        """Convert the string value to its corresponding named element if one exists."""
        for ity in cls:
            if ity.value == ty:
                return ity
        raise ValueError(f"No ModelType {ty}")


default_model_type = {
    QuantumChemicalTopologyProgram.AIMAll: [ModelType.iqa],
    QuantumChemicalTopologyProgram.Morfi: [ModelType.iqa_dispersion],
}

model_types: List[ModelType] = default_model_type[
    QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM()
]
atom_names: List[str] = []


def setup(directory: Path):
    """
    Setup the global variables defining what GPR models to make
    Implemented with global variables to allow for calling from the menu and from the command line
    during auto run, having one setup function for both allows for less code duplication
    """

    global model_data_location
    global _model_data
    global n_training_points
    global atom_names
    global atom_models_to_make

    model_data_location = directory
    _model_data = PointsDirectory(directory)
    n_training_points = len(_model_data)
    atom_names = [atom.name for atom in _model_data[0].atoms]
    atom_models_to_make = list(atom_names)


def toggle_model_type(ty: ModelType):
    global model_types
    if ty in model_types:
        del model_types[model_types.index(ty)]
    else:
        model_types += [ty]


def select_model_type():
    """Select properties for which to make models - these can be any combination of multiple moments and iqa energy."""
    global model_types
    global models_selected
    if not models_selected:
        model_types = []
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
                break
            elif ans in model_type_list:
                if ans == "multipoles":
                    for multipole in constants.multipole_names:
                        if multipole in model_type_list:
                            toggle_model_type(ModelType[multipole])
                else:
                    toggle_model_type(ModelType[ans])
            elif ans in ["c", "clear"]:
                model_types.clear()
    models_selected = True


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
    global atom_models_to_make
    if atom in atom_models_to_make:
        del atom_models_to_make[atom_models_to_make.index(atom)]
    else:
        atom_models_to_make += [atom]


def select_atoms():
    global atom_models_to_make
    global atoms_selected
    if not atoms_selected:
        atom_models_to_make = []
    with ListCompleter(atom_names):
        while True:
            print("Select Atoms To Create Models For")
            for atom in atom_names:
                print(f"[{'x'if atom in atom_models_to_make else ' '}] {atom}")
            print()
            ans = input(">> ")
            ans = ans.strip()
            if ans == "":
                break
            elif ans in atom_names:
                toggle_atom_model(ans)
            elif ans in ["c", "clear"]:
                atom_models_to_make.clear()
    atoms_selected = True


def make_models_menu_refresh(menu):
    """
    This is a `refresh` function that takes in an instance of a menu and add options to it. See `class Menu` `refresh` attrubute.
    By defining a custom refresh function, when the menu refreshes we can clear the menu options to refresh the messages so they
    update when changed by the user

    :param menu: An instance of `class Menu` to which options are added.
    """
    menu.clear_options()
    menu.add_option("1", "Make Models", create_ferebus_directories_and_submit)
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
    menu.add_message(f"Atoms: {', '.join(map(str, atom_models_to_make))}")
    menu.add_final_options()


def make_models_menu(directory: Path):
    """The handler function for making models from a specific directory. To make the models, both Gaussian and AIMALL have to be ran
    for the points that are in the directory."""
    setup(directory)
    # use context manager here because we need to run the __enter__ and __exit__ methods.
    # Make an instance called `menu` and set its `self.refresh` to `make_models_menu_refresh`, which gets called in the menu's `run` method
    with Menu("Make Models Menu", refresh=make_models_menu_refresh) as menu:
        pass


# todo: I think that the functions could be named better because there is make_models and create_ferebus_directories_and_submit. Also the file could be
# arranged better because make_models is followed by move_models instead of create_ferebus_directories_and_submit. It is hard to understand what is going on due to the use of globals and a lot of functiosn in functions
def make_models(
    directory: Path,
    atoms: Optional[List[str]] = None,
    ntrain: Optional[int] = None,
    types: Optional[List[str]] = None,
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    """Function that is used in auto run to make GP models with FEREBUS. The actual function that makes the needed files is called `create_ferebus_directories_and_submit`.

    :return: The job id of the submitted job
    """
    global model_data_location
    global _model_data
    global n_training_points
    global atom_models_to_make
    global model_types

    model_data_location = directory
    _model_data = PointsDirectory(directory)

    n_training_points = ntrain or len(_model_data)
    model_types = (
        [ModelType.from_str(ty) for ty in types]
        if types is not None
        else [ModelType.iqa]
    )
    atom_models_to_make = atoms or [
        atom.atom_num for atom in _model_data[0].atoms
    ]

    logger.info(
        f"Making Models for {atom_models_to_make} atoms and {model_types} types with {n_training_points} training points"
    )

    return create_ferebus_directories_and_submit(hold=hold)


def move_models(model_dir: Optional[Path] = None):
    """Move model files from the ferebus directory to the models directory."""
    from ichor.file_structure import FILE_STRUCTURE
    from ichor.globals import GLOBALS
    from ichor.models import Model

    mkdir(FILE_STRUCTURE["models"])
    mkdir(FILE_STRUCTURE["model_log"])

    if model_dir is None:
        model_dir = FILE_STRUCTURE["ferebus"]

    for d in model_dir.iterdir():
        if d.is_dir() and d != FILE_STRUCTURE["models"]:
            for f in d.iterdir():
                if f.suffix == ".model":
                    cp(f, FILE_STRUCTURE["models"])
                    model_log = FILE_STRUCTURE[
                        "model_log"
                    ] / GLOBALS.SYSTEM_NAME + str(Model(f).ntrain).zfill(4)
                    logger.info(
                        f"Moving {f} to {FILE_STRUCTURE['models']} and {model_log}"
                    )
                    mkdir(model_log)
                    cp(f, model_log)

        elif d.is_file() and d.suffix == ".model":
            cp(d, FILE_STRUCTURE["models"])
            model_log = FILE_STRUCTURE["model_log"] / (
                GLOBALS.SYSTEM_NAME + str(Model(d).ntrain).zfill(4)
            )
            mkdir(model_log)
            cp(d, model_log)


def create_ferebus_directories_and_submit(
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    """Makes the training set file in a separate directory for each topological atom. Calls `make_ferebus_script` which writes out the ferebus
    job script that needed to run on compute nodes and submits to queue.

    :return: The job id of the submitted job
    """
    ferebus_directories = []

    for atom in atom_models_to_make:
        training_data = []
        features = _model_data[atom].features
        for i, point in enumerate(_model_data):
            properties = {
                ty.value: getattr(point, ty.value)[atom] for ty in model_types
            }
            training_data += [(features[i], properties)]

        ferebus_directory = write_training_set(atom, training_data)
        ferebus_directories += [ferebus_directory]

    return make_ferebus_script(ferebus_directories, hold=hold)


def make_ferebus_script(
    ferebus_directories: List[Path], hold: Optional[JobID] = None
) -> Optional[JobID]:
    """Writes our the ferebus script needed to run a ferebus job and submits to queueing system.

    :return: The job id of the submitted job
    """
    script_name = SCRIPT_NAMES["ferebus"]
    ferebus_script = SubmissionScript(script_name)
    for ferebus_directory in ferebus_directories:
        ferebus_script.add_command(FerebusCommand(ferebus_directory))
    ferebus_script.write()
    return ferebus_script.submit(hold=hold)


def write_training_set(atom, training_data) -> Path:
    """Write training set, containing inputs (such as r, theta, phi features), and outputs (IQA and multipole moments) for one atom.
    Returns the directory in which the training set was written as each atom has its own directory.

    :param atom: The name of the atom for which the training set is made (e.g. C1)
    :param training_data: A list of tuples containing the training data. Each tuple contains the (input, output) pair. The inputs are stored as a numpy array,
        while the outputs are stored as a dictionary, containing key:value paris of property_name (eg. iqa, q00) : value
    """
    from ichor.file_structure import FILE_STRUCTURE
    from ichor.globals import GLOBALS

    # make a ferebus directory for each atom
    ferebus_directory = FILE_STRUCTURE["ferebus"] / atom
    mkdir(ferebus_directory, empty=True)

    training_set_file = (
        ferebus_directory / f"{GLOBALS.SYSTEM_NAME}_{atom}_TRAINING_SET.csv"
    )
    # write config for ferebus
    write_ftoml(ferebus_directory, atom)
    with open(training_set_file, "w") as ts:
        if n_training_points > 0:
            # this part is to get headers for the columns (so f1,f2,f3....,q00,q10,....)
            inputs, outputs = training_data[0]
            input_headers = [f"f{i+1}" for i in range(len(inputs))]
            output_headers = [f"{output}" for output in outputs.keys()]
            ts.write(
                f",{','.join(input_headers)},{','.join(output_headers)}\n"
            )
            # this part is for writing out the features and output values for each point.
            for i, (inputs, outputs) in enumerate(training_data):
                ts.write(
                    f"{i},{','.join(map(str, inputs))},{','.join(map(str, outputs.values()))}\n"
                )

    return ferebus_directory


def write_ftoml(ferebus_directory: Path, atom: str):
    """Write the toml file which holds settings for FEREBUS.

    :param ferebus_directory: A Path object pointing to the directory where the FEREBUS job is going to be ran
    :param atom: A string corresponding to the atom's name (such as C1, H3, etc.)
    """
    from ichor.atoms.calculators.feature_calculator.alf_feature_calculator import \
        ALFFeatureCalculator
    from ichor.globals import GLOBALS

    ftoml_file = ferebus_directory / "ferebus.toml"
    alf = list(np.array(GLOBALS.ALF[get_digits(atom) - 1]) + 1)

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
