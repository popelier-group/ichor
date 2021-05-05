from ichor.menu import Menu


def points_directory_menu(path):
    from ichor.main.submit_gjfs import submit_gjfs
    from ichor.main.submit_wfns import submit_wfns
    from ichor.main.make_models import make_models_menu

    with Menu(f"{path} Menu", space=True, back=True, exit=True) as menu:
        menu.add_option(
            "1", "Submit GJFs to Gaussian", submit_gjfs, kwargs={"directory": path}
        )
        menu.add_option(
            "2", "Submit WFNs to AIMAll", submit_wfns, kwargs={"directory": path}
        )
        menu.add_option(
            "3", "Make Models", make_models_menu, kwargs={"directory": path}
        )


def main_menu() -> None:
    from ichor.globals import GLOBALS
    with Menu("ICHOR Main Menu", space=True, back=True, exit=True) as menu:
        menu.add_option(
            "1",
            "Training Set Menu",
            points_directory_menu,
            kwargs={"path": GLOBALS.FILE_STRUCTURE["training_set"]},
        )
        menu.add_option(
            "2",
            "Sample Pool Menu",
            points_directory_menu,
            kwargs={"path": GLOBALS.FILE_STRUCTURE["sample_pool"]},
        )
        menu.add_option(
            "3",
            "Validation Set Menu",
            points_directory_menu,
            kwargs={"path": GLOBALS.FILE_STRUCTURE["validation_set"]},
        )
