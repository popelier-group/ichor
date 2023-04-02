from consolemenu import ConsoleMenu, SelectionMenu, MultiSelectMenu, MenuFormatBuilder, PromptUtils, Screen, items, clear_terminal
from consolemenu.items import CommandItem, ExitItem, ExternalItem, FunctionItem, MenuItem, SelectionItem, SubmenuItem
from ichor.cli.menu_descriptions import TOOLS_MENU_DESCRIPTION

tools_menu = ConsoleMenu(TOOLS_MENU_DESCRIPTION.title, TOOLS_MENU_DESCRIPTION.prologue_text)
