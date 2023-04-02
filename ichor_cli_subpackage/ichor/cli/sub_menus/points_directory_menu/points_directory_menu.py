from consolemenu import ConsoleMenu, SelectionMenu, MultiSelectMenu, MenuFormatBuilder, PromptUtils, Screen, items, clear_terminal
from consolemenu.items import CommandItem, ExitItem, ExternalItem, FunctionItem, MenuItem, SelectionItem, SubmenuItem
from ichor.cli.menu_descriptions import POINTS_DIRECTORY_MENU_DESCRIPTION

points_directory_menu = ConsoleMenu(POINTS_DIRECTORY_MENU_DESCRIPTION.title, POINTS_DIRECTORY_MENU_DESCRIPTION.prologue_text)
