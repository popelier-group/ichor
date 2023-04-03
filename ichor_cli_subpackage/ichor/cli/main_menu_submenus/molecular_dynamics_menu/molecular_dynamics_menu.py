from consolemenu import ConsoleMenu, SelectionMenu, MultiSelectMenu, MenuFormatBuilder, PromptUtils, Screen, items, clear_terminal
from consolemenu.items import CommandItem, ExitItem, ExternalItem, FunctionItem, MenuItem, SelectionItem, SubmenuItem
from ichor.cli.menu_descriptions import MenuDescription

MOLECULAR_DYNAMICS_MENU_DESCRIPTION = MenuDescription("Molecular Dynamics Menu", "Use this to do submit MD simulations with ichor.")
molecular_dynamics_menu = ConsoleMenu(MOLECULAR_DYNAMICS_MENU_DESCRIPTION.title, MOLECULAR_DYNAMICS_MENU_DESCRIPTION.prologue_text)
