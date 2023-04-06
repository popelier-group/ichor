from consolemenu import ConsoleMenu, SelectionMenu, MultiSelectMenu, MenuFormatBuilder, PromptUtils, Screen, items, clear_terminal
from consolemenu.items import CommandItem, ExitItem, ExternalItem, FunctionItem, MenuItem, SelectionItem, SubmenuItem
from ichor.cli.menu_description import MenuDescription

TOOLS_MENU_DESCRIPTION = MenuDescription("Tools Menu", subtitle="Use this to run quick useful ichor functions.")
tools_menu = ConsoleMenu(
                        title=TOOLS_MENU_DESCRIPTION.title,
                        subtitle=TOOLS_MENU_DESCRIPTION.subtitle,
                        prologue_text = TOOLS_MENU_DESCRIPTION.prologue_description_text,
                        epilogue_text=TOOLS_MENU_DESCRIPTION.epilogue_description_text,
                        show_exit_option=TOOLS_MENU_DESCRIPTION.show_exit_option)