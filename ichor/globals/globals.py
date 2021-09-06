import inspect
import os
import platform
from pathlib import Path
from typing import List
from uuid import UUID

from ichor import constants
from ichor.arguments import Arguments
from ichor.atoms.atoms import Atoms
from ichor.common import io
from ichor.common.functools import run_once
from ichor.common.types import DictList, Version
from ichor.file_structure import FileStructure
from ichor.globals import checkers, formatters, parsers
from ichor.globals.config_provider import ConfigProvider
from ichor.globals.os import OS
from ichor.problem_finder import ProblemFinder

# todo: automatically generate md table from global variables into 'doc/GLOBALS.md'

"""
Global variables are the backbone of ichor and are used throughout

Mutable global variables are tricky things and should be used with caution, the global variables
defined in Globals are carefully maintained by a series of parsers, formatters and checkers to try
and make sure that the global variable is always valid.

Global Variable                 | Type            | Default Value     | Description                                                                                | Notes
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
SYSTEM_NAME                     | str             | SYSTEM            | Name of the current system                                                                 |
ALF_REFERENCE_FILE              | str             |                   | Path to file containing geometry to calculate ALF                                          | gjf or xyz                                                                                      # todo: convert to Path
ALF                             | List[List[int]] | []                | ALF used for ichor containing atomic indices                                               | 1-index
ATOMS                           | Atoms           | None              | Instance of Atoms from ALF_REFERENCE_FILE                                                  |
CWD                             | Path            | os.getcwd()       | Current working directory                                                                  |
N_ITERATIONS                    | int             | 1                 | Number of iterations to run adaptive sampling for                                          |
POINTS_PER_ITERATION            | int             | 1                 | Number of points to add to training set per iteration                                      |
OPTIMISE_PROPERTY               | str             | iqa               | Atomic property to optimise in adaptive sampling                                           |
OPTIMISE_ATOM                   | str             | all               | Atom to optimise in adaptive sampling                                                      | Can be all or a specific atom
ACTIVE_LEARNING_METHOD          | str             | epe               | Active learning method to use                                                              | Currently only epe is implemented
NORMALISE                       | bool            | False             | Whether to normalise data before running through ferebus                                   | No longer implemented
STANDARDISE                     | bool            | False             | Whether to standardise data before running through ferebus                                 | No longer implemented
METHOD                          | str             | B3LYP             | Quantum mechanics method to use in Gaussian calculation                                    |
BASIS_SET                       | str             | 6-31+g(d,p)       | Basis set to use in Gaussian calculation                                                   |
KEYWORDS                        | List[str]       | []                | Keywords used to run Gaussian                                                              | 
ENCOMP                          | int             | 3                 | Encomp setting to use for AIMAll                                                           | Can be 3 or 4
BOAQ                            | str             | gs20              | Boaq setting used for AIMAll                                                               |
IASMESH                         | str             | fine              | Iasmesh setting used for AIMAll                                                            |
FILE_STRUCTURE                  | FileStructure   | FileStructure     | Object containing all file paths for ichor                                                 | Protected
TRAINING_POINTS                 | int             | 500               | Number of training points to initialise training set with                                  | Not used by min_max or min_max_mean
SAMPLE_POINTS                   | int             | 9000              | Number of sample points to initialise sample pool with                                     |
VALIDATION_POINTS               | int             | 500               | Number of validation points to initialise validation set with                              |
TRAINING_SET_METHOD             | List[str]       | [min_max_mean]    | Methods to initialise training set                                                         | Ran in order of the list                                                                        # todo: implement parser for reading from config
SAMPLE_POOL_METHOD              | List[str]       | [random]          | Methods to initialise sample pool                                                          | Ran in order of the list                                                                        # todo: implement parser for reading from config
VALIDATION_SET_METHOD           | List[str]       | [random]          | Methods to initialise validation set                                                       | Ran in order of the list                                                                        # todo: implement parser for reading from config
KERNEL                          | str             | rbf-cyclic        | Kernel to use in ferebus                                                                   | Can only use rbf-cyclic currently
FEREBUS_TYPE                    | str             | executable        | Tells ichor to run FEREBUS or FEREBUS.py                                                   | Currently executable implemented only                                                           # todo: implement python variant and convert to enum
FEREBUS_VERSION                 | Version         | 7.0               | Current ferebus version                                                                    | Older versions use different training set and config files                                      # todo: reimplement older style for v3
FEREBUS_LOCATION                | Path            | PROGRAMS/FEREBUS  | Path to ferebus executable                                                                 |
GAUSSIAN_MEMORY_LIMIT           | str             | 1GB               | Memory limit for runnning Gaussian
GAUSSIAN_CORE_COUNT             | int             | 2                 | Number of cores to run Gaussian                                                            |
AIMALL_CORE_COUNT               | int             | 2                 | Number of cores to run AIMAll                                                              |
FEREBUS_CORE_COUNT              | int             | 4                 | Number of cores to run FEREBUS                                                             |
DLPOLY_CORE_COUNT               | int             | 1                 | Number of cores to run DLPOLY                                                              |
CP2K_CORE_COUNT                 | int             | 8                 | Number of cores to run CP2K                                                                |
GAUSSIAN_N_TRIES                | int             | 10                | Number of tries to run Gaussian job before giving up                                       | If negative will run infinitely
AIMALL_N_TRIES                  | int             | 10                | Number of tries to run AIMAll job before giving up                                         | If negative will run infinitely
FEREBUS_SWARM_SIZE              | int             | 50                | Swarm size for FEREBUS PSO                                                                 |
FEREBUS_NUGGET                  | float           | 1.0e-10           | Nugget parameter for FEREBUS                                                               |
FEREBUS_THETA_MIN               | float           | 0.0               | Min theta value for PSO initialisation in FEREBUS                                          |
FEREBUS_THETA_MAX               | float           | 3.0               | Max theta value for PSO initialisation in FEREBUS                                          |
MAX_NUGGET                      | float           | 1e-4              | ICHOR v2 iteratively increased nugget value when near singular matrix was encountered      | Can probably delete this # todo: delete MAX_NUGGET
FEREBUS_INERTIA_WEIGHT          | float           | 0.72900           | Inertia weight for FEREBUS PSO                                                             |
FEREBUS_COGNITIVE_LEARNING_RATE | float           | 1.49400           | Cognitive learning rate for FEREBUS PSO                                                    |
FEREBUS_SOCIAL_LEARNING_RATE    | float           | 1.49400           | Social learning rate for FEREBUS PSO                                                       |
FEREBUS_MEAN                    | str             | constant          | Mean function for ferebus to use                                                           | Currently only constant implemented
FEREBUS_OPTIMISATION            | str             | pso               | Optimiser for ferebus                                                                      | Currently only PSO implemented
FEREBUS_TOLERANCE               | float           | 1.0e-8            | Tolerance for relative difference calculation in ferebus PSO                               | 1e-8 is reasonably strict convergence criteria
FEREBUS_STALL_ITERATIONS        | int             | 50                | Stall iterations for relative difference calculation in ferebus PSO                        | 50 is reasonably strict convergence criteria
FEREBUS_CONVERGENCE             | int             | 20                | Old version of FEREBUS_STALL_ITERATIONS                                                    | Can probably delete # todo: delete FEREBUS_CONVERGENCE
FEREBUS_MAX_ITERATION           | int             | 1000              | Number of iterations FEREBUS PSO should run for                                            |
DLPOLY_VERSION                  | Version         | 4.09              | Current DLPOLY version                                                                     | Older versions of DLPOLY used different inputs # todo: reimplement older dlpoly version
DLPOLY_NUMBER_OF_STEPS          | int             | 500               | Number of steps to run DLPOLY simulation for                                               | DLPOLY currently not implemented in v3                                                         # todo: implement interface to DLPOLY
DLPOLY_TEMPERATURE              | int             | 0                 | Temperature to run DLPOLY simulation (K)                                                   | DLPOLY currently not implemented in v3                                                         # todo: implement interface to DLPOLY
DLPOLY_PRINT_EVERY              | int             | 1                 | DLPOLY output prints every `DLPOLY_PRINT_EVERY` timesteps                                  | DLPOLY currently not implemented in v3                                                         # todo: implement interface to DLPOLY
DLPOLY_TIMESTEP                 | float           | 0.001             | Length of timestep in DLPOLY simulation (ps)                                               | DLPOLY currently not implemented in v3                                                         # todo: implement interface to DLPOLY
DLPOLY_LOCATION                 | Path            | PROGRAMS/DLPOLY.Z | Path to DLPOLY executable                                                                  | DLPOLY currently not implemented in v3                                                         # todo: implement interface to DLPOLY
DLPOLY_CHECK_CONVERGENCE        | bool            | False             | Older DLPOLY version allowed for convergence check in geometry optimisations               | DLPOLY currently not implemented in v3                                                         # todo: implement interface to DLPOLY
DLPOLY_CONVERGENCE_CRITERIA     | int             | -1                | Older DLPOLY version allowed for convergence check in geometry optimisations               | DLPOLY currently not implemented in v3                                                         # todo: implement interface to DLPOLY
DLPOLY_MAX_ENERGY               | float           | -1.0              | Older DLPOLY version allowed for convergence check in geometry optimisations               | DLPOLY currently not implemented in v3                                                         # todo: implement interface to DLPOLY
DLPOLY_MAX_FORCE                | float           | -1.0              | Older DLPOLY version allowed for convergence check in geometry optimisations               | DLPOLY currently not implemented in v3                                                         # todo: implement interface to DLPOLY
DLPOLY_RMS_FORCE                | float           | -1.0              | Older DLPOLY version allowed for convergence check in geometry optimisations               | DLPOLY currently not implemented in v3                                                         # todo: implement interface to DLPOLY
DLPOLY_MAX_DISP                 | float           | -1.0              | Older DLPOLY version allowed for convergence check in geometry optimisations               | DLPOLY currently not implemented in v3                                                         # todo: implement interface to DLPOLY
DLPOLY_RMS_DISP                 | float           | -1.0              | Older DLPOLY version allowed for convergence check in geometry optimisations               | DLPOLY currently not implemented in v3                                                         # todo: implement interface to DLPOLY
CP2K_INPUT                      | str             |                   | CP2K input geometry file                                                                   | CP2K interface not implemented in v3                                                           # todo: implement CP2K interface for v3
CP2K_TEMPERATURE                | int             | 300               | Temperature to run CP2K simulation (K)                                                     | CP2K interface not implemented in v3                                                           # todo: implement CP2K interface for v3
CP2K_STEPS                      | int             | 10000             | Number of timesteps to run CP2K simulation for                                             | CP2K interface not implemented in v3                                                           # todo: implement CP2K interface for v3
CP2K_TIMESTEP                   | float           | 1.0               | Length of timestep in CP2K simulation (ps)                                                 | CP2K interface not implemented in v3                                                           # todo: implement CP2K interface for v3
CP2K_METHOD                     | str             | BLYP              | QM method for CP2K simulation                                                              | CP2K interface not implemented in v3                                                           # todo: implement CP2K interface for v3
CP2K_BASIS_SET                  | str             | 6-31G*            | Basis set for CP2K simulation                                                              | CP2K interface not implemented in v3                                                           # todo: implement CP2K interface for v3
CP2K_DATA_DIR                   | str             |                   | Path to CP2K data directory                                                                | CP2K interface not implemented in v3                                                           # todo: implement CP2K interface for v3
WARN_RECOVERY_ERROR             | bool            | True              | Switch on warnings for large recovery errors                                               | Warnings not currently implemented in v3                                                       # todo: implement recovery error warning for v3
RECOVERY_ERROR_THRESHOLD        | float           | 0.00038           | Threshold to warn user about large recover errors (Ha)                                     | Warnings not currently implemented in v3                                                       # todo: implement recovery error warning for v3
WARN_INTEGRATION_ERROR          | bool            | True              | Switch on warnings for large integration errors                                            | Warnings not currently implemented in v3                                                       # todo: implement integration error warning for v3
INTEGRATION_ERROR_THRESHOLD     | float           | 0.001             | Threshold to warn user about large integration erorrs                                      | Warnings not currently implemented in v3                                                       # todo: implement integrations error warning for v3
LOG_WARNINGS                    | bool            | False             | Switch to write warnings to log file                                                       | Warnings not currently implemented in v3                                                       # todo: implement warnings for v3
OS                              | OS              | OS.Linux          | Current operating system                                                                   | Should automatically detect between linux, macos and windows
DISABLE_PROBLEMS                | bool            | False             | Disables showing problems at the top of the main menu                                      | Problems currently not implemented for v3                                                      # todo: implement problems for v3
UID                             | UUID            | Arguments.uid     | Unique ID for ichor instance                                                               | Very important variable for making sure ichor reads and writes data to the correct location
IQA_MODELS                      | bool            | False             | Deprecated variable for older ferebus version to toggle whether ichor is making iqa models | No longer required # todo: delete `IQA_MODELS`
DROP_N_COMPUTE                  | bool            | False             | Toggle whether to use drop-n-compute                                                       | Drop-n-compute not currently implemented for v3                                                # todo: implement drop-n-compute interface for v3
DROP_N_COMPUTE_LOCATION         | Path            |                   | Location of drop-n-compute directory                                                       | Drop-n-compute not currently implemented for v3                                                # todo: implement drop-n-compute interface for v3
GIT_USERNAME                    | str             |                   | Git username for cloning popelier-group repositories                                       | Shouldn't be needed if GIT_TOKEN is defined
GIT_PASSWORD                    | str             |                   | Git password for cloning popelier-group repositories                                       | Git has deprecated use of passwords on remote machines                                         # todo: delete `GIT_PASSWORD`
GIT_TOKEN                       | str             | ghp_...           | Git token for cloning popelier-group repositories                                          |
INCLUDE_NODES                   | List[str]       | []                | Node whitelist for ichor to run jobs on                                                    |
EXCLUDE_NODES                   | List[str]       | []                | Node blacklist for ichor not to run jobs on                                                |
"""


class Globals:
    _types = []

    # Variables that can't be set from config file
    _protected: List[str] = []
    # Variables set in config
    _in_config: List[str] = []
    # Default values for variables
    _defaults = {}
    # Allowed values for variables
    _allowed_values = {}

    # For parsing global variables into type
    _parsers = DictList()
    # For formatting global variables after parsing
    _formatters = DictList()
    # For checking global variables after formatting
    _checkers = DictList()

    SYSTEM_NAME: str = "SYSTEM"
    ALF_REFERENCE_FILE: str = ""  # set automatically if not defined
    ALF: List[List[int]] = []
    ATOMS: Atoms = None

    CWD: Path = Path(os.getcwd())

    N_ITERATIONS: int = 1
    POINTS_PER_ITERATION: int = 1

    OPTIMISE_PROPERTY: str = "iqa"
    OPTIMISE_ATOM: str = "all"

    ACTIVE_LEARNING_METHOD: str = "epe"

    NORMALISE: bool = False
    STANDARDISE: bool = False

    METHOD: str = "B3LYP"
    BASIS_SET: str = "6-31+g(d,p)"
    KEYWORDS: List[str] = []

    ENCOMP: int = 3
    BOAQ: str = "gs20"
    IASMESH: str = "fine"

    FILE_STRUCTURE: FileStructure = FileStructure()  # Don't change

    TRAINING_POINTS: int = 500
    SAMPLE_POINTS: int = 9000
    VALIDATION_POINTS: int = 500

    TRAINING_SET_METHOD: List[str] = ["min_max_mean"]
    SAMPLE_POOL_METHOD: List[str] = ["random"]
    VALIDATION_SET_METHOD: List[str] = ["random"]

    KERNEL: str = "rbf-cyclic"  # rbf or rbf-cyclic currently
    FEREBUS_TYPE: str = (
        "executable"  # executable (FEREBUS) or python (FEREBUS.py)
    )
    FEREBUS_VERSION: Version = Version("7.0")
    FEREBUS_LOCATION: Path = Path("PROGRAMS/FEREBUS")

    GAUSSIAN_MEMORY_LIMIT: str = "1GB"

    # CORE COUNT SETTINGS FOR RUNNING PROGRAMS (SUFFIX CORE_COUNT)
    GAUSSIAN_CORE_COUNT: int = 2
    AIMALL_CORE_COUNT: int = 2
    FEREBUS_CORE_COUNT: int = 4
    DLPOLY_CORE_COUNT: int = 1
    CP2K_CORE_COUNT: int = 8

    # N TRIES SETTINGS FOR RETRYING TO RUN PROGRAMS
    GAUSSIAN_N_TRIES: int = 10
    AIMALL_N_TRIES: int = 10

    FEREBUS_SWARM_SIZE: int = (
        50  # If negative >> Size dynamically allocated by FEREBUS
    )
    FEREBUS_NUGGET: float = 1.0e-10  # Default value for FEREBUS nugget
    FEREBUS_THETA_MIN: float = (
        0.0  # Minimum theta value for initialisation (best to keep 0)
    )
    FEREBUS_THETA_MAX: float = 3.0  # Maximum theta value for initialisation

    MAX_NUGGET: float = 1e-4

    FEREBUS_INERTIA_WEIGHT: float = 0.72900
    FEREBUS_COGNITIVE_LEARNING_RATE: float = 1.49400
    FEREBUS_SOCIAL_LEARNING_RATE: float = 1.49400

    FEREBUS_MEAN: str = "constant"
    FEREBUS_OPTIMISATION: str = "pso"

    FEREBUS_TOLERANCE: float = 1.0e-8
    FEREBUS_STALL_ITERATIONS: int = 50
    FEREBUS_CONVERGENCE: int = 20
    FEREBUS_MAX_ITERATION: int = 1000

    # DLPOLY RUNTIME SETTINGS (PREFIX DLPOLY)
    DLPOLY_VERSION: Version = Version("4.09")

    DLPOLY_NUMBER_OF_STEPS: int = 500  # Number of steps to run simulation for
    DLPOLY_TEMPERATURE: int = (
        0  # If set to 0, will perform geom opt but default to 10 K
    )
    DLPOLY_PRINT_EVERY: int = 1  # Print trajectory and stats every n steps
    DLPOLY_TIMESTEP: float = 0.001  # in ps
    DLPOLY_LOCATION: Path = Path("PROGRAMS/DLPOLY.Z")

    DLPOLY_CHECK_CONVERGENCE: bool = False
    DLPOLY_CONVERGENCE_CRITERIA: int = -1

    DLPOLY_MAX_ENERGY: float = -1.0
    DLPOLY_MAX_FORCE: float = -1.0
    DLPOLY_RMS_FORCE: float = -1.0
    DLPOLY_MAX_DISP: float = -1.0
    DLPOLY_RMS_DISP: float = -1.0

    # CP2K SETTINGS
    CP2K_INPUT: str = ""
    CP2K_TEMPERATURE: int = 300  # K
    CP2K_STEPS: int = 10000
    CP2K_TIMESTEP: float = 1.0  # fs
    CP2K_METHOD: str = "BLYP"
    CP2K_BASIS_SET: str = "6-31G*"
    CP2K_DATA_DIR: str = ""

    # Recovery and Integration Errors
    WARN_RECOVERY_ERROR: bool = True
    RECOVERY_ERROR_THRESHOLD: float = (
        1.0 / constants.ha_to_kj_mol
    )  # Ha (1.0 kJ/mol)

    WARN_INTEGRATION_ERROR: bool = True
    INTEGRATION_ERROR_THRESHOLD: float = 0.001

    # Activate Warnings when making models
    LOG_WARNINGS: bool = False  # Gets set in _make_models

    OS: OS = OS.Linux

    DISABLE_PROBLEMS: bool = False
    UID: UUID = Arguments.uid

    IQA_MODELS: bool = False

    DROP_N_COMPUTE: bool = False
    DROP_N_COMPUTE_LOCATION: Path = ""

    GIT_USERNAME: str = ""
    GIT_PASSWORD: str = ""
    GIT_TOKEN: str = " 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"

    INCLUDE_NODES: List[str] = []
    EXCLUDE_NODES: List[str] = []

    def __init__(self):
        # check types
        for global_variable in self.global_variables:
            if global_variable not in self.__annotations__.keys():
                self.__annotations__[global_variable] = type(
                    self.get(global_variable)
                )

        self.UID = Arguments.uid

        # Set Protected Variables
        self._protected = [
            "FILE_STRUCTURE",
            "SGE",
            "SUBMITTED",
            "UID",
            "IQA_MODELS",
            "MACHINE",
            "OS",
            "ATOMS",
        ]

        # Setup Parsers
        for global_variable in self.global_variables:
            global_type = self.__annotations__[global_variable]
            if global_type is str:
                self._parsers[global_variable] += [parsers.parse_str]
            elif global_type is bool:
                self._parsers[global_variable] += [parsers.parse_bool]
            elif global_type is int:
                self._parsers[global_variable] += [parsers.parse_int]
            elif global_type is float:
                self._parsers[global_variable] += [parsers.parse_float]
            elif global_type is Path:
                self._parsers[global_variable] += [parsers.read_path]

        self._parsers["KEYWORDS"] += [parsers.split_keywords]
        self._parsers["ALF"] += [parsers.read_alf]
        self._parsers["FEREBUS_VERSION"] += [parsers.read_version]
        self._parsers["DLPOLY_VERSION"] += [parsers.read_version]

        self._parsers["INCLUDE_NODES"] += [parsers.split_keywords]
        self._parsers["EXCLUDE_NODES"] += [parsers.split_keywords]

        self._parsers["UID"] += [parsers.read_uid]

        # TODO: Parsers to add
        # - Training/Sample/Validation Set methods
        # - Make sure List[int] is parsed correctly

        # Setup Formatters
        for global_variable in self.global_variables:
            global_type = self.__annotations__[global_variable]
            if global_type is str:
                self._formatters[global_variable] += [formatters.cleanup_str]

        self._formatters["SYSTEM_NAME"] += [formatters.to_upper]
        self._formatters["OPTIMISE_PROPERTY"] += [formatters.to_lower]

        # Setup Checkers
        self._allowed_values = {
            "METHOD": constants.GAUSSIAN_METHODS,
            "BOAQ": constants.BOAQ_VALUES,
            "IASMESH": constants.IASMESH_VALUES,
            "FEREBUS_TYPE": constants.FEREBUS_TYPES,
            "OPTIMISE_PROPERTY": ["iqa"] + constants.multipole_names,
            "KERNEL": constants.KERNELS,
        }

        # TODO: Checks to add
        # - Basis Set (not sure how to do this one)
        # - Optimise Atom, must be done after determining system
        # - Check FEREBUS Location
        # - Check DLPOLY Location
        # - FEREBUS Mean
        # - FEREBUS Optimiser
        # - CP2K Method
        # - CP2K Basis Set

        for variable, allowed_values in self._allowed_values.items():
            self._checkers[variable] += [
                lambda val, av=allowed_values: checkers.check_allowed(val, av)
            ]

        self._checkers["MAX_ITERATION"] += [checkers.positive]
        self._checkers["POINTS_PER_ITERATION"] += [checkers.positive]
        self._checkers["TRAINING_POINTS"] += [checkers.positive_or_zero]
        self._checkers["SAMPLE_POINTS"] += [checkers.positive_or_zero]
        self._checkers["VALIDATION_POINTS"] += [checkers.positive_or_zero]

        self._checkers["FEREBUS_SWARM_SIZE"] += [checkers.positive]
        self._checkers["FEREBUS_NUGGET"] += [checkers.positive]
        self._checkers["FEREBUS_INERTIA_WEIGHT"] += [checkers.positive]
        self._checkers["FEREBUS_COGNITIVE_LEARNING_RATE"] += [
            checkers.positive
        ]
        self._checkers["FEREBUS_SOCIAL_LEARNING_RATE"] += [checkers.positive]
        self._checkers["FEREBUS_TOLERANCE"] += [checkers.positive]
        self._checkers["FEREBUS_STALL_ITERATIONS"] += [checkers.positive]
        self._checkers["FEREBUS_CONVERGENCE"] += [checkers.positive]
        self._checkers["FEREBUS_MAX_ITERATION"] += [checkers.positive]

        self._checkers["DLPOLY_NUMBER_OF_STEPS"] += [checkers.positive]
        self._checkers["DLPOLY_TEMPERATURE"] += [checkers.positive_or_zero]
        self._checkers["DLPOLY_PRINT_EVERY"] += [checkers.positive]
        self._checkers["DLPOLY_TIMESTEP"] += [checkers.positive]

        self._checkers["CP2K_TEMPERATURE"] += [checkers.positive]
        self._checkers["CP2K_STEPS"] += [checkers.positive]
        self._checkers["CP2K_TIMESTEP"] += [checkers.positive]

        # Setup Defaults
        for global_variable in self.global_variables:
            self._defaults[global_variable] = self.get(global_variable)

    @staticmethod
    @run_once
    def define():
        globals_instance = Globals()
        globals_instance.init()
        return globals_instance

    def init(self):
        # Set OS
        if platform == "linux" or platform == "linux2":
            self.OS = OS.Linux
        elif platform == "darwin":
            self.OS = OS.MacOS
        elif platform == "win32":
            self.OS = OS.Windows

        # Uncomment this when drop-n-compute is activated
        # # Add to list of drop-n-compute-services as they're added
        # if self.MACHINE in ["csf3"]:
        #     self.DROP_N_COMPUTE = True

        config = ConfigProvider(source=Arguments.config_file)

        for key, val in config.items():
            if key in self.global_variables:
                self.set(key, val)
                self._in_config += [key]
            elif key in [
                "MAX_ITERATION",
                "N_ITERATION",
            ]:  # Deprecated variable names
                self.set("N_ITERATIONS", val)
                self._in_config += ["N_ITERATIONS"]
            else:
                ProblemFinder.unknown_settings += [key]

        # if (
        #     self.DROP_N_COMPUTE
        #     and not self.DROP_N_COMPUTE_LOCATION
        #     and self.MACHINE == "csf3"
        # ):
        #     self.DROP_N_COMPUTE_LOCATION = Path.home() / "DropCompute"
        # if self.DROP_N_COMPUTE_LOCATION:
        #     io.mkdir(self.DROP_N_COMPUTE_LOCATION)

        if self.FILE_STRUCTURE["training_set"].exists():
            from ichor.files import GJF

            for d in self.FILE_STRUCTURE["training_set"].iterdir():
                if d.is_dir():
                    for f in d.iterdir():
                        if f.suffix == ".gjf":
                            self.ATOMS = GJF(f).atoms
                            break
                elif d.is_file() and d.suffix == ".gjf":
                    self.ATOMS = GJF(d).atoms
                    break
        else:
            from ichor.files import Trajectory

            for f in Path(os.getcwd()).iterdir():
                if f.suffix == ".xyz":
                    traj = Trajectory(f)
                    traj.read(n=1)
                    self.ATOMS = traj[0]

    def set(self, name, value):
        name = name.upper()
        if name not in self.global_variables:
            ProblemFinder.unknown_settings.append(name)
        elif name in self._protected:
            ProblemFinder.protected_settings.append(name)
        else:
            try:
                setattr(self, name, value)
            except ValueError as e:
                ProblemFinder.incorrect_settings[name] = e

    def get(self, name):
        return getattr(self, name, None)

    def items(self, show_protected=False):
        return [
            (global_variable, getattr(self, global_variable))
            for global_variable in self.global_variables
            if global_variable not in self._protected or show_protected
        ]

    def save_to_properties_config(self, config_file, global_variables):
        with open(config_file, "w") as config:
            config.write(f"{constants.ichor_logo}\n\n")
            for key, val in global_variables.items():
                if str(val) in ["[]", "None"]:
                    continue
                config.write(f"{key}={val}\n")

    def save_to_yaml_config(self, config_file, global_variables):
        import yaml

        with open(config_file, "w") as config:
            yaml.dump(global_variables, config)

    def save_to_config(self, config_file: str = Arguments.config_file):
        global_variables = {
            global_variable: global_value
            for global_variable, global_value in self.items()
            if (
                global_value != self._defaults[global_variable]
                or global_variable in self._in_config
            )
        }

        if config_file.endswith(".properties"):
            self.save_to_properties_config(config_file, global_variables)
        elif config_file.endswith(".yaml"):
            self.save_to_yaml_config(config_file, global_variables)

    @property
    def config_variables(self):
        return [
            g for g in self.global_variables if g in self._in_config.keys()
        ]

    @property
    def global_variables(self):

        try:
            return self._global_variables
        except AttributeError:
            methods = [
                f[0]
                for f in inspect.getmembers(
                    Globals, predicate=inspect.isfunction
                )
            ]
            properties = [
                p[0]
                for p in inspect.getmembers(
                    Globals, lambda o: isinstance(o, property)
                )
            ]
            methods += properties
            self._global_variables = [
                key
                for key in dir(self)
                if not key.startswith("_") and key not in methods
            ]

            return self._global_variables

    def __setattr__(self, name, value):
        if (
            hasattr(self, "_global_variables")
            and name in self.global_variables
        ):
            for parser in self._parsers.get(name, []):
                value = parser(value)
            for formatter in self._formatters.get(name, []):
                value = formatter(value)
            for check in self._checkers.get(name, []):
                check(value)  # Should raise error if incorrect

            if name == "ALF":
                Atoms.ALF = (
                    value  # Make sure Atoms.ALF and GLOBALS.ALF are synced
                )

        super(Globals, self).__setattr__(name, value)
