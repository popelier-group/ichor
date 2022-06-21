import sys

from ichor.cli.analysis_menus import (
    analysis_menu,
    dlpoly_menu,
    geometry_analysis,
    rmse_menu,
    s_curve_menu,
)
from ichor.cli.general_menus import (
    concatenate_points_menu,
    edit_globals_menu,
    options_menu,
    queue_menu,
    rotate_mol,
)
from ichor.cli.points_directory_menu import points_directory_menu
from ichor.cli.machine_learning_menus import (
    make_models,
    per_atom_menu,
    per_menu,
)
from ichor.cli.main_menu import main_menu
from ichor.cli.molecular_dynamics_menus import amber, cp2k, md_menu, tyche
from ichor.core.common.types import Version
from ichor.hpc import GLOBALS, Arguments

from ichor.hpc import ichor_main

__version__ = Version("3.1.0")


def ichor_cli():
    ichor_main()
    main_menu()
