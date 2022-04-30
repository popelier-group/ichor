from pathlib import Path
from typing import List, Optional

import numpy as np

from ichor.ichor_lib import constants
from ichor.batch_system import JobID
from ichor.ichor_lib.common.io import cp, mkdir
from ichor.ichor_lib.common.str import get_digits
from ichor.ichor_hpc.file_structure.file_structure import FILE_STRUCTURE
from ichor.ichor_lib.files import PointsDirectory
from ichor.globals import GLOBALS
from ichor.log import logger
from ichor.ichor_cli.menus.menu import Menu
from ichor.models import Model
from ichor.qct import (QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM,
                       QuantumChemicalTopologyProgram)
from ichor.submission_script import (SCRIPT_NAMES, FerebusCommand,
                                     SubmissionScript)
from ichor.ichor_cli.menus.tab_completer import ListCompleter

model_data_location: Path = Path()
_model_data: Optional[PointsDirectory] = None
n_training_points: int = 0
atom_models_to_make: List[str] = []

atoms_selected = False
models_selected = False


def MODEL_TYPES() -> List[str]:
    _model_types = [
        "iqa",
        *constants.multipole_names,
    ]

    if (
        QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM()
        is QuantumChemicalTopologyProgram.Morfi
    ):
        _model_types += [
            "dispersion"
        ]  # dispersion only available when qctp is morfi
    return _model_types


default_model_type = "iqa"
atom_names: List[str] = []

model_types = [default_model_type]


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


def toggle_model_type(ty: str):
    global model_types
    if ty in model_types:
        del model_types[model_types.index(ty)]
    else:
        model_types += [ty]


def toggle_add_dispersion():
    GLOBALS.ADD_DISPERSION_TO_IQA = not GLOBALS.ADD_DISPERSION_TO_IQA


def select_model_type():
    """Select properties for which to make models - these can be any combination of multiple moments and iqa energy."""
    global model_types
    global models_selected
    if not models_selected:
        model_types = []
    while True:
        Menu.clear_screen()
        print("Select Models To Create")
        _model_types = MODEL_TYPES()
        model_type_list = _model_types + ["multipoles"]
        with ListCompleter(model_type_list + ["all", "c", "clear"]):
            for ty in _model_types:
                print(f"[{'x' if ty in model_types else ' '}] {ty}")
            print()
            ans = input(">> ")
            ans = ans.strip().lower()
            if ans == "":
                break
            elif ans in model_type_list:
                if ans == "multipoles":
                    for multipole in constants.multipole_names:
                        if multipole in model_type_list:
                            toggle_model_type(multipole)
                else:
                    toggle_model_type(ans)
            elif ans == "all":
                model_types = list(_model_types)
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
    with ListCompleter(atom_names + ["all", "c", "clear"]):
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
            elif ans == "all":
                atom_models_to_make = list(atom_names)
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
    if (
        QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM()
        is QuantumChemicalTopologyProgram.Morfi
    ):
        menu.add_option(
            "d", "Toggle Add Dispersion to IQA", toggle_add_dispersion
        )
    menu.add_space()
    menu.add_message(f"Model Type(s): {', '.join(model_types)}")
    menu.add_message(f"Number of Training Points: {n_training_points}")
    menu.add_message(f"Atoms: {', '.join(map(str, atom_models_to_make))}")
    if (
        QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM()
        is QuantumChemicalTopologyProgram.Morfi
    ):
        menu.add_message(
            f"Add Dispersion to IQA: {GLOBALS.ADD_DISPERSION_TO_IQA}"
        )
    menu.add_final_options()


def make_models_menu(directory: Path):
    """The handler function for making models from a specific directory. To make the models, both Gaussian and AIMALL have to be ran
    for the points that are in the directory."""
    setup(directory)
    # use context manager here because we need to run the __enter__ and __exit__ methods.
    # Make an instance called `menu` and set its `self.refresh` to `make_models_menu_refresh`, which gets called in the menu's `run` method
    with Menu("Make Models Menu", refresh=make_models_menu_refresh) as menu:
        pass


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
        [ty for ty in types] if types is not None else [default_model_type]
    )
    atom_models_to_make = atoms or [atom.name for atom in _model_data[0].atoms]

    logger.info(
        f"Making Models for {atom_models_to_make} atoms and {model_types} types with {n_training_points} training points"
    )

    return create_ferebus_directories_and_submit(hold=hold)


def move_models(model_dir: Optional[Path] = None):
    """Move model files from the ferebus directory to the models directory."""
    if model_dir is None:
        model_dir = FILE_STRUCTURE["ferebus"]

    for d in model_dir.iterdir():
        if d.is_dir() and d != FILE_STRUCTURE["models"]:
            move_models(d)
        elif d.is_file() and d.suffix == Model.filetype:
            _move_model(d)


def _move_model(f: Path):
    mkdir(FILE_STRUCTURE["models"])
    mkdir(FILE_STRUCTURE["model_log"])

    cp(f, FILE_STRUCTURE["models"])
    model_log = FILE_STRUCTURE["model_log"] / (
        GLOBALS.SYSTEM_NAME + str(Model(f).ntrain).zfill(4)
    )
    mkdir(model_log)
    cp(f, model_log)


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
            # if a point does not have int files in it this will fail.
            # point[atom] is an AtomData instance. Usually, an INT is used as self.properties attribute
            # of AtomData. Then INT is subclasses from GeometryDataFile (where get_property is locateds)
            try:
                properties = {
                    ty: point[atom].get_property(ty) for ty in model_types
                }
                training_data += [(features[i], properties)]
            except:
                logger.warning(f"Failed to get property information for point {point.path.absolute()}. Check if .int \
                    files from AIMALL are present in it.")

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
    from ichor.ichor_hpc.file_structure.file_structure import FILE_STRUCTURE
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
    from ichor.globals import GLOBALS

    ftoml_file = ferebus_directory / "ferebus.toml"
    alf = list(np.array(GLOBALS.ALF[get_digits(atom) - 1]) + 1)

    # todo: probably best to remake this in a smarter way
    nfeats = 3*len(GLOBALS.ATOMS)-6
    rbf_dims = list(range(1, nfeats+1))
    per_dims = [i for i in rbf_dims if i > 3 and i % 3 == 0]
    rbf_dims = list(set(rbf_dims) - set(per_dims))

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
        if GLOBALS.KERNEL.lower() in ["rbf", "rbf-cyclic"]:
            ftoml.write(f'kernel = "k1"\n')
        elif GLOBALS.KERNEL.lower() == "periodic":
            ftoml.write(f'kernel = "k1*k2"\n')
        if GLOBALS.STANDARDISE:
            ftoml.write(f"standardise = true\n")
        #ftoml.write(f'likelihood = "{GLOBALS.FEREBUS_LIKELIHOOD}"\n')
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
        if GLOBALS.KERNEL.lower() in ["rbf", "rbf-cyclic"]:
            ftoml.write("[kernels.k1]\n")
            ftoml.write(f'type = "{GLOBALS.KERNEL}"\n')
        elif GLOBALS.KERNEL.lower() == "periodic":
            ftoml.write("[kernels.k1]\n")
            ftoml.write(f'type = "rbf"\n')
            ftoml.write(f'active_dimensions = {rbf_dims}\n')
            ftoml.write("\n")
            ftoml.write("[kernels.k2]\n")
            ftoml.write('type = "periodic"\n')
            ftoml.write(f'active_dimensions = {per_dims}\n')
        ftoml.write("\n")
        ftoml.write("[notes]\n")
        ftoml.write(f'method = "{GLOBALS.METHOD}"\n')
        ftoml.write(f'basis-set = "{GLOBALS.BASIS_SET}"\n')
        if (
            "iqa" in model_types
            and QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM()
            is QuantumChemicalTopologyProgram.Morfi
        ):
            iqa = "iqa+dispersion" if GLOBALS.ADD_DISPERSION_TO_IQA else "iqa"
            ftoml.write(f'iqa = "{iqa}"\n')
