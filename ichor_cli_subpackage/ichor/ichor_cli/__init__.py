import sys
from ichor.ichor_hpc.batch_system import BATCH_SYSTEM
from ichor.ichor_lib.common.types import Version
from ichor.ichor_hpc.globals import GLOBALS
from ichor.ichor_hpc.machine_setup.machine_setup import MACHINE
from ichor.ichor_hpc.arguments import Arguments
from ichor.ichor_hpc.globals import GLOBALS
from ichor.ichor_cli.menus import main_menu

__version__ = Version("3.0.1")


def ichor_main():
    from ichor.ichor_hpc import in_main

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