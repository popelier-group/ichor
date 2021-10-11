import importlib
import sys
from argparse import ArgumentParser
from ast import literal_eval
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence, Tuple
from uuid import UUID

from ichor.common.bool import check_bool
from ichor.common.uid import get_uid


class ExternalFunction:
    """
    Class to contain information for adding an ichor function to be able to be ran externally
    e.g.
    python ichor3.py -f submit_gjfs TRAINING_SET
    """

    def __init__(self, module: str, function: str, name: Optional[str] = None):
        """
        Constructor for ExternalFunction, think of arguments in terms of the import statement

        ```python
        from {module} import {function} as {name}
        ```

        :param module: module to import from
        :param function: function to import from module
        :param name: the name which the function will be called externally, defaults to the name of the function
        """
        self.module = module
        self.function = function
        self.name = name or self.function

    def import_function(self):
        m = importlib.import_module(self.module)
        return getattr(m, self.function)


# todo: these will need updating because the paths/names are updated
# List of all ichor external functions, add functions to the list. Note: a checker for these has not been implemented
external_functions = [
    ExternalFunction("ichor.logging", "log_time"),
    ExternalFunction("ichor.main.active_learning", "active_learning"),
    ExternalFunction("ichor.main.collate_log", "collate_model_log"),
    ExternalFunction("ichor.main.make_models", "make_models, move_models"),
    ExternalFunction(
        "ichor.main.submit_gjfs", "submit_points_directory_to_gaussian"
    ),
    ExternalFunction("ichor.main.gaussian", "rerun_gaussian"),
    ExternalFunction("ichor.main.gaussian", "scrub_gaussian"),
    ExternalFunction("ichor.main.aimall", "rerun_aimall"),
    ExternalFunction("ichor.main.aimall", "scrub_aimall"),
    ExternalFunction("ichor.main.submit_wfns", "submit_wfns"),
    ExternalFunction("ichor.main.submit_wfns", "check_aimall_output"),
    ExternalFunction("ichor.make_sets", "make_sets"),
    ExternalFunction("ichor.submission_script", "print_completed"),
    ExternalFunction(
        "ichor.analysis.dlpoly", "run_dlpoly_geometry_optimisations"
    ),
    ExternalFunction("ichor.analysis.dlpoly", "get_dlpoly_energies"),
    ExternalFunction(
        "ichor.analysis.dlpoly", "submit_final_geometry_to_gaussian"
    ),
    ExternalFunction(
        "ichor.main.pandora", "copy_aimall_wfn_to_point_directory"
    ),
    ExternalFunction("ichor.main.amber", "mdcrd_to_xyz"),
]

# Convert list of external functions to a dictionary of external functions with the name of each function as the key
external_functions = {ef.name: ef for ef in external_functions}


class Arguments:
    """Used to parse command line arguments that are given to ICHOR. These arguments are given using `-` or `--` and read with argparse."""

    config_file: Path = Path("config.properties")
    uid: UUID = get_uid()
    auto_run: bool = False

    call_external_function = None
    call_external_function_args = []

    @staticmethod
    def read():
        parser = ArgumentParser(description="ICHOR: A kriging training suite")

        parser.add_argument(
            "-c",
            "--config",
            dest="config_file",
            type=str,
            help="Name of Config File for ICHOR",
        )
        allowed_functions = ", ".join(map(str, external_functions.keys()))
        parser.add_argument(
            "-f",
            "--func",
            dest="func",
            type=str,
            metavar=("func", "arg"),
            nargs="+",
            help=f"Call ichor function with args, allowed functions: [{allowed_functions}]",
        )
        parser.add_argument(
            "-u",
            "--uid",
            dest="uid",
            type=str,
            help="Unique Identifier For ichor Jobs To Write To",
        )

        parser.add_argument(
            "-ar",
            "--autorun",
            dest="autorun",
            default=False,
            action="store_true",
            help="Flag used to specify ichor is running in auto-run mode",
        )

        args = parser.parse_args()
        if args.config_file:
            Arguments.config_file = Path(args.config_file)

        if args.func:
            func = args.func[0]
            func_args = args.func[1:] if len(args.func) > 1 else []
            if func in external_functions.keys():
                Arguments.call_external_function = external_functions[
                    func
                ].import_function()
                Arguments.call_external_function_args = parse_args(
                    func=Arguments.call_external_function, args=func_args
                )
            else:
                print(f"{func} not in allowed functions:")
                formatted_functions = [
                    str(f) for f in allowed_functions.split(",")
                ]
                formatted_functions = ", ".join(formatted_functions)
                print(f"{formatted_functions}")
                sys.exit(0)

        if args.uid:
            Arguments.uid = args.uid

        Arguments.auto_run = args.autorun


def parse_args(func: Callable, args: List[str]) -> List[Any]:
    """
    Takes in func and returns properly parsed arguments
    Argument types are retrieved from type annotations and can be one of the following:
    - str
    - int
    - float
    - bool
    - List
    - None
    - Path
    - Optional
    - Union
    """

    if not func.__annotations__:
        return args

    for i, (arg, arg_type) in enumerate(
        zip(args, func.__annotations__.values())
    ):
        args[i] = parse_arg(arg, arg_type)

    return args


def parse_arg(arg, arg_type) -> Any:
    if arg_type is str:
        return str(arg)
    elif arg_type is Path:
        return Path(arg)
    elif arg_type is int:
        return int(arg)
    elif arg_type is float:
        return float(arg)
    elif arg_type is bool:
        return check_bool(arg)
    elif hasattr(arg_type, "__args__"):
        # From typing (Optional, List)
        if len(arg_type.__args__) == 2 and arg_type.__args__[-1] is type(None):
            # Optional argument
            if arg == "None":
                return None
            else:
                return parse_arg(arg, arg_type.__args__[0])
        elif isinstance(arg_type, (type(Sequence), type(List), type(Tuple))):
            # Sequence of type arg_type.__args__[0]
            return [
                parse_arg(a, arg_type.__args__[0]) for a in literal_eval(arg)
            ]
        else:
            # Union
            for at in arg_type.__args__:
                try:
                    return parse_arg(arg, at)
                except TypeError:
                    pass

    raise TypeError(f"Cannot parse argument '{arg}' of type '{arg_type}'")
