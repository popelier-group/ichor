from pathlib import Path
from typing import Optional, List, Tuple, Dict
import numpy as np
from ichor.hpc.batch_system import JobID
from ichor.core.models import Model
from ichor.core.files import PointsDirectory
from ichor.hpc.log import logger
from ichor.core.common.io import mkdir, cp
from ichor.hpc.submission_script import (
    SubmissionScript,
    SCRIPT_NAMES,
    FerebusCommand,
)
from ichor.core.common.str import get_digits
from ichor.hpc.programs.qct import (
    QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM,
    QuantumChemicalTopologyProgram,
)
from ichor.core import constants


default_model_type = "iqa"


def MODEL_TYPES() -> List[str]:
    model_types = [
        "iqa",
        *constants.multipole_names,
    ]

    if (
        QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM()
        is QuantumChemicalTopologyProgram.Morfi
    ):
        model_types += [
            "dispersion",
            "iqa+dispersion"
        ]  # dispersion only available when qctp is morfi
    return model_types


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

    model_data = PointsDirectory(directory)

    n_training_points = ntrain or len(model_data)
    model_types = list(types) if types is not None else [default_model_type]
    atom_models_to_make = atoms or [atom.name for atom in model_data[0].atoms]

    logger.info(
        f"Making Models for {atom_models_to_make} atoms and {model_types} types with {n_training_points} training points"
    )

    return create_ferebus_directories_and_submit(model_data, atoms, types, n_training_points, hold=hold)


def move_models(model_dir: Optional[Path] = None):
    from ichor.hpc import FILE_STRUCTURE

    """Move model files from the ferebus directory to the models directory."""
    if model_dir is None:
        model_dir = FILE_STRUCTURE["ferebus"]

    for d in model_dir.iterdir():
        if d.is_dir() and d != FILE_STRUCTURE["models"]:
            move_models(d)
        elif d.is_file() and d.suffix == Model.filetype:
            _move_model(d)


def _move_model(f: Path):
    from ichor.hpc import FILE_STRUCTURE, GLOBALS

    mkdir(FILE_STRUCTURE["models"])
    mkdir(FILE_STRUCTURE["model_log"])

    cp(f, FILE_STRUCTURE["models"])
    model_log = FILE_STRUCTURE["model_log"] / (
        GLOBALS.SYSTEM_NAME + str(Model(f).ntrain).zfill(4)
    )
    mkdir(model_log)
    cp(f, model_log)


def create_ferebus_directories_and_submit(
    model_data: PointsDirectory,
    atoms: List[str],
    model_types: List[str],
    n_training_points: Optional[int] = None,
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    """Makes the training set file in a separate directory for each topological atom. Calls `make_ferebus_script` which writes out the ferebus
    job script that needed to run on compute nodes and submits to queue.

    :return: The job id of the submitted job
    """
    ferebus_directories = []
    n_training_points = n_training_points or len(model_data)

    for atom in atoms:
        training_data = []
        features = model_data[atom].features()
        for i, point in enumerate(model_data):
            # if a point does not have int files in it this will fail.
            # point[atom] is an AtomData instance. Usually, an INT is used as self.properties attribute
            # of AtomData. Then INT is subclasses from GeometryDataFile (where get_property is locateds)
            try:
                properties = {
                    ty: point[atom].get_property(ty) for ty in model_types
                }
                training_data.append((features[i], properties))
            except AttributeError:
                logger.warning(
                    f"Failed to get property information for point {point.path.absolute()}. Check if .int \
                    files from AIMALL are present in it."
                )

        ferebus_directory = write_training_set(
            atom, training_data, n_training_points
        )
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


def write_training_set(
    atom: str,
    training_data: List[Tuple[np.ndarray, Dict[str, float]]],
    n_training_points: int,
) -> Path:
    """Write training set, containing inputs (such as r, theta, phi features), and outputs (IQA and multipole moments) for one atom.
    Returns the directory in which the training set was written as each atom has its own directory.

    :param atom: The name of the atom for which the training set is made (e.g. C1)
    :param training_data: A list of tuples containing the training data. Each tuple contains the (input, output) pair. The inputs are stored as a numpy array,
        while the outputs are stored as a dictionary, containing key:value paris of property_name (eg. iqa, q00) : value
    :param n_training_points: Number of training points to use of the training_data
    """
    from ichor.hpc import FILE_STRUCTURE, GLOBALS

    # make a ferebus directory for each atom
    ferebus_directory = FILE_STRUCTURE["ferebus"] / atom
    mkdir(ferebus_directory, empty=True)

    training_set_file = (
        ferebus_directory / f"{GLOBALS.SYSTEM_NAME}_{atom}_TRAINING_SET.csv"
    )
    # write config for ferebus
    model_types = list(training_data[0][1].keys()) if training_data else []
    write_ftoml(ferebus_directory, atom, model_types)
    with open(training_set_file, "w") as ts:
        if n_training_points > 0:
            # this part is to get headers for the columns (so f1,f2,f3....,q00,q10,....)
            inputs, outputs = training_data[0]
            input_headers = [f"f{i + 1}" for i in range(len(inputs))]
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


def write_ftoml(ferebus_directory: Path, atom: str, model_types: List[str]):
    """Write the toml file which holds settings for FEREBUS.

    :param ferebus_directory: A Path object pointing to the directory where the FEREBUS job is going to be ran
    :param atom: A string corresponding to the atom's name (such as C1, H3, etc.)
    :param model_types: List of model types (str) being trained
    """
    from ichor.hpc import GLOBALS

    ftoml_file = ferebus_directory / "ferebus.toml"
    alf = list(np.array(GLOBALS.ALF[get_digits(atom) - 1]) + 1)

    # todo: probably best to remake this in a smarter way
    nfeats = 3 * len(GLOBALS.ATOMS) - 6
    rbf_dims = list(range(1, nfeats + 1))
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
        if GLOBALS.KERNEL.lower() in ["rbf", "rbf-cyclic"] or nfeats < 6:
            ftoml.write(f'kernel = "k1"\n')
        elif GLOBALS.KERNEL.lower() == "periodic":
            ftoml.write(f'kernel = "k1*k2"\n')
        if GLOBALS.STANDARDISE:
            ftoml.write(f"standardise = true\n")
        # ftoml.write(f'likelihood = "{GLOBALS.FEREBUS_LIKELIHOOD}"\n')
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
        kernel = "rbf-cyclic" if GLOBALS.KERNEL == "rbf-cyclic" else "rbf"
        ftoml.write("[kernels.k1]\n")
        ftoml.write(f'type = "{kernel}"\n')
        if nfeats > 6 and GLOBALS.KERNEL == "periodic":
            ftoml.write(f"active_dimensions = {rbf_dims}\n")
            ftoml.write("\n")
            ftoml.write("[kernels.k2]\n")
            ftoml.write('type = "periodic"\n')
            ftoml.write(f"active_dimensions = {per_dims}\n")
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
