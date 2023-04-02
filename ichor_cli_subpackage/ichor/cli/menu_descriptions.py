from dataclasses import dataclass

@dataclass
class MenuDescription:
    """ Dataclass for menu descriptions. The descriptions of new menus will be added here."""
    title: str
    prologue_text: str = ""
    epilogue_text: str = ""
    show_exit_option: bool = False

MAIN_MENU_DESCRIPTION = MenuDescription("Main Menu", "Welcome to ichor's main menu!", show_exit_option=True)
POINTS_DIRECTORY_MENU_DESCRIPTION = MenuDescription("PointsDirectory Menu", "Use this to do interact with ichor's PointsDirectory class.")
ANALYSIS_MENU_DESCRIPTION = MenuDescription("Analysis Menu", "Use this to do analysis of data with ichor.")
MOLECULAR_DYNAMICS_MENU_DESCRIPTION = MenuDescription("Molecular Dynamics Menu", "Use this to do submit MD simulations with ichor.")
TOOLS_MENU_DESCRIPTION = MenuDescription("Tools Menu", "Use this to run quick useful ichor functions.")
