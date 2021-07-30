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
from ichor.globals.machine import Machine
from ichor.problem_finder import ProblemFinder


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

    ADAPTIVE_SAMPLING_METHOD: str = "epe"

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

    # todo: thought we were using normal rbf kernel
    KERNEL: str = "rbf-cyclic"  # rbf or rbf-cyclic currently
    FEREBUS_TYPE: str = (
        "executable"  # executable (FEREBUS) or python (FEREBUS.py)
    )
    FEREBUS_VERSION: Version = Version("7.0")
    FEREBUS_LOCATION: Path = Path("PROGRAMS/FEREBUS")

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

    MACHINE: Machine = ""
    SGE: bool = False  # Don't Change
    SUBMITTED: bool = False  # Don't Change

    DISABLE_PROBLEMS: bool = False
    UID: UUID = Arguments.uid

    IQA_MODELS: bool = False

    DROP_N_COMPUTE: bool = False
    DROP_N_COMPUTE_LOCATION: Path = ""

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
        # Set Machine Name
        machine_name = platform.node()
        if "csf3." in machine_name:
            self.MACHINE = Machine.csf3
        elif "ffluxlab" in machine_name:
            self.MACHINE = Machine.ffluxlab
        else:
            self.MACHINE = Machine.local

        # Uncomment this when drop-n-compute is activated
        # # Add to list of drop-n-compute-services as they're added
        # if self.MACHINE in ["csf3"]:
        #     self.DROP_N_COMPUTE = True

        # TODO: Remove need for SGE, abstract over batch systems
        # SGE settings
        self.SGE = "SGE_ROOT" in os.environ.keys()
        self.SUBMITTED = "SGE_O_HOST" in os.environ.keys()

        config = ConfigProvider(source=Arguments.config_file)

        for key, val in config.items():
            if key in self.global_variables:
                self.set(key, val)
                self._in_config += [key]
            else:
                ProblemFinder.unknown_settings += [key]

        if (
            self.DROP_N_COMPUTE
            and not self.DROP_N_COMPUTE_LOCATION
            and self.MACHINE == "csf3"
        ):
            self.DROP_N_COMPUTE_LOCATION = Path.home() / "DropCompute"
        if self.DROP_N_COMPUTE_LOCATION:
            io.mkdir(self.DROP_N_COMPUTE_LOCATION)

        # todo: why is the training set structure generated in Globals?
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

    def save_to_config(self, config_file=Arguments.config_file):
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
        # todo: remove import because it is not used
        from optparse import OptionParser

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
