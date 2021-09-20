"""Open the main menu for ICHOR when running `python ichor3.py`. From there, the user can select what jobs to run."""
from ichor.arguments import Arguments
from ichor.globals import GLOBALS, Globals
from ichor.main import main_menu
import warnings
import sys

warnings.filterwarnings("ignore", category=FutureWarning)   # regex string in WFN.read() issues warning of recurssive group, will likely change WFN parsing in future and remove this

if __name__ == '__main__':
    from ichor import in_main

    in_main.IN_MAIN = True

    Arguments.read()
    GLOBALS.init_from_config(Arguments.config_file)
    GLOBALS.UID = Arguments.uid
    if Arguments.call_external_function:
        Arguments.call_external_function(
            *Arguments.call_external_function_args
        )
        sys.exit(0)

    main_menu()
