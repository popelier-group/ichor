from ichor.main.tools_menu import tools_menu
from ichor.main.queue import queue_menu
from ichor.menu import Menu


def points_directory_menu(path):
    from ichor.main.make_models import make_models_menu
    from ichor.main.submit_gjfs import submit_gjfs
    from ichor.main.submit_wfns import submit_wfns

    with Menu(f"{path} Menu", space=True, back=True, exit=True) as menu:
        menu.add_option(
            "1",
            "Submit GJFs to Gaussian",
            submit_gjfs,
            kwargs={"directory": path}, # which directory to submit gjfs from (TRAINING_SET, SAMPLE_POOL, etc.)
        )
        menu.add_option(
            "2",
            "Submit WFNs to AIMAll",
            submit_wfns,
            kwargs={"directory": path}, # which directory to submit AIMALLs from (TRAINING_SET, SAMPLE_POOL, etc.)
        )
        menu.add_option(
            "3", "Make Models", make_models_menu, kwargs={"directory": path} # which directory to make models from (TRAINING_SET, SAMPLE_POOL, etc.)
        )


def main_menu() -> None:
    """Initialize the main menu Command Line Interface (CLI) for ICHOR."""

    from ichor.auto_run import auto_run
    from ichor.globals import GLOBALS
    from ichor.main.adaptive_sampling import adaptive_sampling

    # initialize an instance of Menu called menu
    with Menu("ICHOR Main Menu", space=True, back=False, exit=True) as menu:
        # add options to the instance `menu`
        menu.add_option(
            "1",
            "Training Set Menu",
            points_directory_menu,
            # give key word arguments which are passed to the handler function
            # the handler function in this case is points_directory_menu. See the Menu class for details.
            kwargs={"path": GLOBALS.FILE_STRUCTURE["training_set"]},  # get the Path of the training set from GLOBALS
        )
        menu.add_option(
            "2",
            "Sample Pool Menu",
            points_directory_menu,
            kwargs={"path": GLOBALS.FILE_STRUCTURE["sample_pool"]},  # get the Path of the sample pool from GLOBALS
        )
        menu.add_option(
            "3",
            "Validation Set Menu",
            points_directory_menu,
            kwargs={"path": GLOBALS.FILE_STRUCTURE["validation_set"]},  # get the Path of the validation set from GLOBALS
        )
        menu.add_option(
            "4",
            "Adaptive Sampling",
            adaptive_sampling,
            kwargs={
                "model_directory": GLOBALS.FILE_STRUCTURE["models"],
                "sample_pool_directory": GLOBALS.FILE_STRUCTURE["sample_pool"],
            },
        )
        menu.add_space()
        menu.add_option(
            "r", "Auto Run", auto_run,
        )
        menu.add_space()
        menu.add_option("t", "Tools Menu", tools_menu)
        menu.add_option("q", "Queue Menu", queue_menu)
