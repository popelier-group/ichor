# from consolemenu import ConsoleMenu, SelectionMenu, MultiSelectMenu, MenuFormatBuilder, PromptUtils, Screen, items, clear_terminal
# from consolemenu.items import CommandItem, ExitItem, ExternalItem, FunctionItem, MenuItem, SelectionItem, SubmenuItem
from ichor.cli.menu_description import MenuDescription
from ichor.cli.submenu_item import ConsoleMenu

ANALYSIS_MENU_DESCRIPTION = MenuDescription("Analysis Menu", subtitle="Use this to do analysis of data with ichor.")
analysis_menu = ConsoleMenu(title=ANALYSIS_MENU_DESCRIPTION.title,
                            subtitle=ANALYSIS_MENU_DESCRIPTION.subtitle,
                            prologue_text = ANALYSIS_MENU_DESCRIPTION.prologue_description_text,
                            epilogue_text=ANALYSIS_MENU_DESCRIPTION.epilogue_description_text,
                            show_exit_option=ANALYSIS_MENU_DESCRIPTION.show_exit_option)
