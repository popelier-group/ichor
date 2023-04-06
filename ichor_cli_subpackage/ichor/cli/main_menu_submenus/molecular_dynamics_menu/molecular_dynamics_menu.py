from consolemenu import ConsoleMenu, SelectionMenu, MultiSelectMenu, MenuFormatBuilder, PromptUtils, Screen, items, clear_terminal
from consolemenu.items import CommandItem, ExitItem, ExternalItem, FunctionItem, MenuItem, SelectionItem, SubmenuItem
from ichor.cli.menu_description import MenuDescription

MOLECULAR_DYNAMICS_MENU_DESCRIPTION = MenuDescription("Molecular Dynamics Menu", subtitle="Use this to submit MD simulations with ichor.")

molecular_dynamics_menu = ConsoleMenu(title=MOLECULAR_DYNAMICS_MENU_DESCRIPTION.title,
                            subtitle=MOLECULAR_DYNAMICS_MENU_DESCRIPTION.subtitle,
                            prologue_text = MOLECULAR_DYNAMICS_MENU_DESCRIPTION.prologue_description_text,
                            epilogue_text=MOLECULAR_DYNAMICS_MENU_DESCRIPTION.epilogue_description_text,
                            show_exit_option=MOLECULAR_DYNAMICS_MENU_DESCRIPTION.show_exit_option)