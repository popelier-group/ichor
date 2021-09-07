from ichor.main.options_menu import options_menu
from ichor.main.queue import queue_menu
from ichor.main.tools_menu import tools_menu
from ichor.menu import Menu


def points_directory_menu(path):
    """Menu that shows up when the user wants to run jobs for a particular Points directory, such as the training set directory,
    validation set directory, or sample pool directory.

    :param path: A Path object to the directory for which the menu is about.
    """
    from ichor.main.make_models import make_models_menu
    from ichor.main.submit_gjfs import submit_gjfs
    from ichor.main.submit_wfns import submit_wfns

    with Menu(f"{path} Menu", space=True, back=True, exit=True) as menu:
        menu.add_option(
            "1",
            "Submit GJFs to Gaussian",
            submit_gjfs,
            kwargs={
                "directory": path
            },  # which directory to submit gjfs from (TRAINING_SET, SAMPLE_POOL, etc.). Set by GLOBALS.FILE_STRUCTURE
        )
        menu.add_option(
            "2",
            "Submit WFNs to AIMAll",
            submit_wfns,
            kwargs={"directory": path},
        )
        menu.add_option(
            "3", "Make Models", make_models_menu, kwargs={"directory": path}
        )


def main_menu() -> None:
    """Initialize the main menu Command Line Interface (CLI) for ICHOR. Other menus can then be accessed from this main menu."""
    from ichor.auto_run import auto_run
    from ichor.file_structure import FILE_STRUCTURE
    from ichor.main.active_learning import adaptive_sampling
    from ichor.main.per_menu import auto_run_per_menu

    # initialize an instance of Menu called menu and add construct the menu in the context manager
    with Menu("ICHOR Main Menu", space=True, back=False, exit=True) as menu:
        # add options to the instance `menu`
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
            "Adaptive Sampling",
            adaptive_sampling,
            kwargs={
                "model_directory": FILE_STRUCTURE["models"],
                "sample_pool_directory": FILE_STRUCTURE["sample_pool"],
            },
        )
        menu.add_space()  # add a blank line
        menu.add_option(
            "r",
            "Auto Run",
            auto_run,
        )
        menu.add_option("p", "Per-Value Auto Run", auto_run_per_menu)
        menu.add_space()
        menu.add_option("t", "Tools Menu", tools_menu)
        menu.add_option("o", "Options Menu", options_menu)
        menu.add_option("q", "Queue Menu", queue_menu)
