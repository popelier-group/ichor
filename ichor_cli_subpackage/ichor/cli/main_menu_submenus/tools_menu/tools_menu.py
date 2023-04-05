from consolemenu import ConsoleMenu, SelectionMenu, MultiSelectMenu, MenuFormatBuilder, PromptUtils, Screen, items, clear_terminal
from consolemenu.items import CommandItem, ExitItem, ExternalItem, FunctionItem, MenuItem, SelectionItem, SubmenuItem
from ichor.cli.menu_description import MenuDescription

TOOLS_MENU_DESCRIPTION = MenuDescription("Tools Menu", subtitle="Use this to run quick useful ichor functions.")
tools_menu = ConsoleMenu(TOOLS_MENU_DESCRIPTION.title, TOOLS_MENU_DESCRIPTION.subtitle)
