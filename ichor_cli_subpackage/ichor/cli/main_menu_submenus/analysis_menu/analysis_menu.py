from ichor.cli.console_menu import ConsoleMenu
from ichor.cli.menu_description import MenuDescription

ANALYSIS_MENU_DESCRIPTION = MenuDescription(
    "Analysis Menu", subtitle="Use this to do analysis of data with ichor."
)
analysis_menu = ConsoleMenu(
    title=ANALYSIS_MENU_DESCRIPTION.title,
    subtitle=ANALYSIS_MENU_DESCRIPTION.subtitle,
    prologue_text=ANALYSIS_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=ANALYSIS_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=ANALYSIS_MENU_DESCRIPTION.show_exit_option,
)
