from argparse import ArgumentParser
from ichor.common.uid import get_uid
from ichor.common.functools import run_once

from uuid import UUID


def import_external_functions():
    # Place functions to run externally in here
    # from ichor.debugging import printq

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
        allowed_functions = "\n".join(
            f"- {func}" for func in Arguments.external_functions.keys()
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
                Arguments.call_external_function = Arguments.external_functions[
                    func
                ]
                Arguments.call_external_function_args = func_args
            else:
                print(f"{func} not in allowed functions:")
                formatted_functions = [
                    str(f) for f in allowed_functions.split(",")
                ]
                formatted_functions = "- " + "\n- ".join(formatted_functions)
                print(f"{formatted_functions}")
                quit()

        if args.uid:
            Arguments.uid = args.uid

    def __enter__(self):
        Arguments.read()

    def __exit__(self, type, value, traceback):
        if Arguments.call_external_function:
            Arguments.call_external_function(*Arguments.call_external_function_args)
