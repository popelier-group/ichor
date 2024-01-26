import platform

from pathlib import Path

import yaml

from ichor.core.common.types import FileTree, FileType

from ichor.hpc.batch_system import init_batch_system
from ichor.hpc.batch_system.parallel_environment import ParallelEnvironment
from ichor.hpc.log import setup_logger
from ichor.hpc.submission_script.script_names import ScriptNames
from ichor.hpc.useful_functions import get_current_python_environment_path, init_machine


try:
    __building_docs__ = __sphinx_build__
except NameError:
    __building_docs__ = False


class MissingIchorConfig(Exception):
    """Exception for missing ichor config file"""

    pass


def get_param_from_config(ichor_config: dict, *keys, default=None):
    """Given a config and keys, this loops over

    :param ichor_config: ichor read in config
    :param keys: positional arguments which to pass to the config
    """

    # shallow copy should be fine because we are not modifying and inner objects
    next_param = ichor_config.copy()

    for k in keys:

        next_param = next_param.get(k)

        # if key is not there, get() will return None by default
        if next_param is None:

            return default

    return next_param


def initialize_config(config_path):
    """
    Reads the ichor config file and sets up where to find modules and executables for programs.
    """

    with open(config_path, "r") as s:
        ichor_config = yaml.safe_load(s)

    return ichor_config


ICHOR_CONFIG_PATH: Path = Path.home() / "ichor_config.yaml"
# check that config file exists

if not ICHOR_CONFIG_PATH.exists():
    if not __building_docs__:
        raise MissingIchorConfig(
            "The ichor_config.yaml file is not found in the home directory. Please add it in order to use ichor.hpc"
        )

if not __building_docs__:
    ICHOR_CONFIG: dict = initialize_config(ICHOR_CONFIG_PATH)
else:
    ICHOR_CONFIG = None

# the MACHINE will be a key from the top layer of the config file
MACHINE: str = init_machine(platform.node(), ICHOR_CONFIG)
if not MACHINE:
    if not __building_docs__:
        raise ValueError("The current machine is not defined in the config file.")

# make parallel environment variables to run jobs on multiple cores
PARALLEL_ENVIRONMENT = ParallelEnvironment()
# if you do not specify parallel environments in config, then error out with KeyError
# make the possible parallel environments for the current machine which ichor is launched on
if not __building_docs__:
    try:
        for p_env_name, values in ICHOR_CONFIG[MACHINE]["hpc"][
            "parallel_environments"
        ].items():
            PARALLEL_ENVIRONMENT[p_env_name] = values
    except KeyError:
        raise KeyError(
            "The parallel environments are not defined for the current machine."
        )

# default file structure to be used for file handling
FILE_STRUCTURE = FileTree()

FILE_STRUCTURE.add(
    ".DATA",
    "data",
    type_=FileType.Directory,
    description="""Directory that contains important information for jobs submitted to
    compute nodes. Submission scripts as well as job outputs among other things are stored here.""",
)

FILE_STRUCTURE.add(
    "SCRIPTS",
    "scripts",
    parent="data",
    type_=FileType.Directory,
    description="""Stores submission scripts which are used to submit
    jobs to compute nodes. Submission scripts are shell (.sh) files such as GAUSSIAN.sh and AIMALL.sh.""",
)

FILE_STRUCTURE.add(
    "OUTPUTS",
    "outputs",
    parent="scripts",
    type_=FileType.Directory,
    description="""This directory contains the standard output (stdout) that the job
    produces. Things like print statements which are written to standard
    output are going to be written here (if ran from a compute node).
        These files have the '.o' extension.""",
)
FILE_STRUCTURE.add(
    "ERRORS",
    "errors",
    parent="scripts",
    type_=FileType.Directory,
    description="""Contains standard error (stderr) which a job script/program has
    produced. These files have the '.e' extension""",
)
FILE_STRUCTURE.add(
    "JOBS",
    "jobs",
    parent="data",
    type_=FileType.Directory,
    description="""Directory containing information about jobs submitted to the
    queueing system.""",
)
FILE_STRUCTURE.add(
    "jid",
    "jid",
    parent="jobs",
    type_=FileType.File,
    description="""A file containing job IDs of jobs submitted to the queueing system.""",
)
FILE_STRUCTURE.add(
    "DATAFILES",
    "datafiles",
    parent="jobs",
    type_=FileType.Directory,
    description="""A directory containing datafiles, which
    have information for paths to inputs and outputs of a calculation submitted
    to the computer cluster. These datafiles are used to give
        the paths to input/output files to jobs without hard-coding
        the inputs/outputs in the job script itself.""",
)
FILE_STRUCTURE.add(
    "CP2K",
    "cp2k",
    type_=FileType.Directory,
    description="""Contains files relating to the molecular dynamics package CP2K.""",
)
# todo: a better description for these two is needed
FILE_STRUCTURE.add(
    "DLPOLY",
    "dlpoly",
    type_=FileType.Directory,
    description="""Directory with files relating to DLPOLY simulations.""",
)
FILE_STRUCTURE.add("GJF", "dlpoly_gjf", parent="dlpoly", type_=FileType.Directory)
FILE_STRUCTURE.add("AMBER", "amber", type_=FileType.Directory)

# batch system on current machine
BATCH_SYSTEM = init_batch_system()

# set up loggers
LOGGER = setup_logger("ICHOR", "ichor.log")

# set up script names that are implemented
SCRIPT_NAMES = ScriptNames(
    {
        "pd_to_database": "pd_to_database.sh",
        "calculate_features": "calculate_features.sh",
        "center_trajectory": "center_trajectory.sh",
        "gaussian": "GAUSSIAN.sh",
        "orca": "ORCA.sh",
        "aimall": "AIMALL.sh",
        "ferebus": "FEREBUS.sh",
        "ichor": ScriptNames(
            {
                "gaussian": "ICHOR_GAUSSIAN.sh",
                "aimall": "ICHOR_AIMALL.sh",
                "ferebus": "ICHOR_FEREBUS.sh",
                "active_learning": "ICHOR_ACTIVE_LEARNING.sh",
                "make_sets": "ICHOR_MAKE_SETS.sh",
                "collate_log": "ICHOR_COLLATE_LOG.sh",
                "dlpoly": ScriptNames(
                    {
                        "setup": "ICHOR_DLPOLY_SETUP.sh",
                        "gaussian": "ICHOR_DLPOLY_GAUSSIAN.sh",
                        "energies": "ICHOR_DLPOLY_ENERGIES.sh",
                    },
                    parent=FILE_STRUCTURE["scripts"],
                ),
                "pandora": ScriptNames(
                    {
                        "pyscf": "ICHOR_PANDORA_PYSCF.sh",
                        "morfi": "ICHOR_PANDORA_MORFI.sh",
                    },
                    parent=FILE_STRUCTURE["scripts"],
                ),
            },
            parent=FILE_STRUCTURE["scripts"],
        ),
        "pandora": ScriptNames(
            {"pyscf": "PANDORA_PYSCF.sh", "morfi": "PANDORA_MORFI.sh"},
            parent=FILE_STRUCTURE["scripts"],
        ),
        "dlpoly": "DLPOLY.sh",
        "dlpoly_gaussian": "ICHOR_DLPOLY_GAUSSIAN.sh",
        "amber": "AMBER.sh",
        "cp2k": "CP2K.sh",
        "opt": ScriptNames(
            {"gaussian": "GEOM_OPT.sh", "convert": "GEOM_OPT_CONVERT.sh"},
            parent=FILE_STRUCTURE["scripts"],
        ),
        "analysis": ScriptNames(
            {"geometry": "GEOMETRY_ANALYSIS.sh", "rotate-mol": "ROTATE_MOL.sh"},
            parent=FILE_STRUCTURE["scripts"],
        ),
    },
    parent=FILE_STRUCTURE["scripts"],
)


# set up current python environment
CURRENT_PYTHON_ENVIRONMENT_PATH = get_current_python_environment_path()
