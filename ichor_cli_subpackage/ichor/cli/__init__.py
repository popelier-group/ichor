import sys

from ichor.cli.analysis_menus import (analysis_menu, dlpoly_menu,
                                            geometry_analysis, rmse_menu,
                                            s_curve_menu)
from ichor.cli.general_menus import (concatenate_points_menu,
                                           edit_globals_menu, options_menu,
                                           points_directory_menu, queue_menu,
                                           rotate_mol)
from ichor.cli.machine_learning_menus import (make_models, per_atom_menu,
                                                    per_menu)
from ichor.cli.main_menu import main_menu
from ichor.cli.molecular_dynamics_menus import (amber, cp2k, md_menu,
                                                      tyche)

from ichor.cli.main_menu import main_menu
from ichor.core.common.types import Version
from ichor.hpc import GLOBALS, Arguments


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
