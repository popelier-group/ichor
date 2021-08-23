import sys
from argparse import ArgumentParser
from ast import literal_eval
from pathlib import Path
from typing import Any, Callable, List, Sequence, Tuple
from uuid import UUID

from ichor.common.bool import check_bool
from ichor.common.functools import run_once
from ichor.common.uid import get_uid


def import_external_functions():
    # Place functions to run externally in here
    from ichor.logging import log_time
    from ichor.main.adaptive_sampling import adaptive_sampling
    from ichor.main.make_models import make_models, move_models
    from ichor.main.submit_gjfs import check_gaussian_output, submit_gjfs
    from ichor.main.submit_wfns import check_aimall_output, submit_wfns
    from ichor.make_sets import make_sets
    from ichor.submission_script import print_completed
    from ichor.main.collate_log import collate_model_log

    Arguments.external_functions = locals()


class Arguments:
    config_file: str = "config.properties"
    uid: UUID = get_uid()

    external_functions = {}
    call_external_function = None
    call_external_function_args = []

    @staticmethod
    @run_once
    def read():
        import_external_functions()

        parser = ArgumentParser(description="ICHOR: A kriging training suite")

        parser.add_argument(
            "-c",
            "--config",
            dest="config_file",
            type=str,
            help="Name of Config File for ICHOR",
        )
        allowed_functions = ", ".join(
            map(str, Arguments.external_functions.keys())
        )
        parser.add_argument(
            "-f",
            "--func",
            dest="func",
            type=str,
            metavar=("func", "arg"),
            nargs="+",
            help=f"Call ICHOR function with args, allowed functions: [{allowed_functions}]",
        )
        parser.add_argument(
            "-u",
            "--uid",
            dest="uid",
            type=str,
            help="Unique Identifier For ICHOR Jobs To Write To",
        )

        args = parser.parse_args()
        if args.config_file:
            Arguments.config_file = args.config_file

        if args.func:
            func = args.func[0]
            func_args = args.func[1:] if len(args.func) > 1 else []
            if func in Arguments.external_functions.keys():
                Arguments.call_external_function = (
                    Arguments.external_functions[func]
                )
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

    def __enter__(self):
        Arguments.read()

    def __exit__(self, type, value, traceback):
        if Arguments.call_external_function:
            Arguments.call_external_function(
                *Arguments.call_external_function_args
            )
            sys.exit(0)


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
