from __future__ import print_function

from pathlib import Path
from typing import List, Optional

from ichor.cli.analysis_menus.analysis_menu import analysis_menu
from ichor.cli.general_menus.options_menu import options_menu
from ichor.cli.points_directory_menu import (
    custom_points_directory_menu, points_directory_menu)
from ichor.cli.general_menus.queue_menu import queue_menu
from ichor.cli.machine_learning_menus.make_models import make_models_menu
from ichor.cli.machine_learning_menus.per_menu import auto_run_per_menu
from ichor.core.menu.menu import Menu
from ichor.hpc import FILE_STRUCTURE
from ichor.hpc.auto_run.standard_auto_run import auto_run_from_menu
from ichor.hpc.main.active_learning import active_learning

_points_directory_path = None
_force = False


# def old_main_menu(subdirs: Optional[List[Path]] = None) -> None:
#     """Initialize the main menu Command Line Interface (CLI) for ICHOR. Other menus can then be accessed from this main menu."""
#
#     # initialize an instance of Menu called menu and add construct the menu in the context manager
#     with Menu(
#         "ICHOR Main Menu",
#         enable_problems=True,
#         space=True,
#         back=False,
#         exit=True,
#         run_in_subdirectories=subdirs,
#     ) as menu:
#         # add options to the instance `menu`
#         menu.add_option(
#             "1",
#             "Training Set Menu",
#             # the handler function in this case is points_directory_menu. This function gets called when the user selects option 1 in the menu.
#             points_directory_menu,
#             # give key word arguments which are passed to the handler function
#             kwargs={
#                 "path": FILE_STRUCTURE["training_set"]
#             },  # get the Path of the training set from GLOBALS.FILE_STRUCTURE
#         )
#         menu.add_option(
#             "2",
#             "Sample Pool Menu",
#             points_directory_menu,
#             kwargs={"path": FILE_STRUCTURE["sample_pool"]},
#         )
#         menu.add_option(
#             "3",
#             "Validation Set Menu",
#             points_directory_menu,
#             kwargs={"path": FILE_STRUCTURE["validation_set"]},
#         )
#         menu.add_option(
#             "4",
#             "Active Learning",
#             active_learning,
#             kwargs={
#                 "model_directory": FILE_STRUCTURE["models"],
#                 "sample_pool_directory": FILE_STRUCTURE["sample_pool"],
#             },
#         )
#         menu.add_space()  # add a blank line
#         menu.add_option(
#             "r",
#             "Auto Run",
#             auto_run_from_menu,
#         )
#         menu.add_option("p", "Per-Value Auto Run", auto_run_per_menu)
#         menu.add_space()
#         menu.add_option(
#             "c", "Custom PointsDirectory Menu", custom_points_directory_menu
#         )
#         menu.add_option("a", "Analysis Menu", analysis_menu)
#         menu.add_option("o", "Options Menu", options_menu)
#         menu.add_option("q", "Queue Menu", queue_menu)


def main():
    menu = Menu("ICHOR Main Menu")
    menu.add_option(
        "1",
        "Training Set Menu",
        # the handler function in this case is points_directory_menu. This function gets called when the user selects option 1 in the menu.
        points_directory_menu,
        # give key word arguments which are passed to the handler function
        kwargs={
            "path": FILE_STRUCTURE["training_set"]
        },  # get the Path of the training set from GLOBALS.FILE_STRUCTURE
    )
    menu.add_option(
        "2",
        "Sample Pool Menu",
        points_directory_menu,
        kwargs={"path": FILE_STRUCTURE["sample_pool"]},
    )
    menu.add_option(
        "3",
        "Validation Set Menu",
        points_directory_menu,
        kwargs={"path": FILE_STRUCTURE["validation_set"]},
    )
    menu.add_option(
        "4",
        "Active Learning",
        active_learning,
        kwargs={
            "model_directory": FILE_STRUCTURE["models"],
            "sample_pool_directory": FILE_STRUCTURE["sample_pool"],
        },
    )
    menu.add_blank()  # add a blank line
    menu.add_option(
        "r",
        "Auto Run",
        auto_run_from_menu,
    )
    menu.add_option("p", "Per-Value Auto Run", auto_run_per_menu)
    menu.add_blank()
    menu.add_option(
        "c", "Custom PointsDirectory Menu", custom_points_directory_menu
    )
    menu.add_option("a", "Analysis Menu", analysis_menu)
    menu.add_option("o", "Options Menu", options_menu)
    menu.add_option("q", "Queue Menu", queue_menu)
    menu.add_final_options(back=False)
    menu.run()


def main_menu():
    main()
