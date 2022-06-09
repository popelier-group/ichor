import sys

from ichor.cli.menus import main_menu
from ichor.core.common.types import Version
from ichor.hpc import BATCH_SYSTEM, GLOBALS, MACHINE, Arguments

__version__ = Version("3.1.0")


def ichor_main():
    from ichor.hpc import in_main

    in_main.IN_MAIN = True

    # TODO: need to reload package, so that other places this is imported has changes made.

    Arguments.read()
    GLOBALS.init_from_config(Arguments.config_file)
    GLOBALS.UID = Arguments.uid
    if Arguments.call_external_function:
        Arguments.call_external_function(
            *Arguments.call_external_function_args
        )
        sys.exit(0)

    main_menu()
