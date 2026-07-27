from dataclasses import dataclass

from consolemenu.items import SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.tools_menu.tools_submenus import (
    points_directory_tools_menu,
    POINTS_DIRECTORY_TOOLS_MENU_DESCRIPTION,
)
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions


TOOLS_MENU_DESCRIPTION = MenuDescription(
    "Tools Menu", subtitle="Use this to run quick useful ichor functions."
)


# the tools menu itself holds no options; each tool has its own submenu with its own
# options, so keep an empty MenuOptions here (submenus display their parents' options,
# so this must not carry any PointsDirectory-specific warnings)
@dataclass
class ToolsMenuOptions(MenuOptions):
    pass


# initialize dataclass for storing information for menu
tools_menu_options = ToolsMenuOptions()


tools_menu = ConsoleMenu(
    this_menu_options=tools_menu_options,
    title=TOOLS_MENU_DESCRIPTION.title,
    subtitle=TOOLS_MENU_DESCRIPTION.subtitle,
    prologue_text=TOOLS_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=TOOLS_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=TOOLS_MENU_DESCRIPTION.show_exit_option,
)


# make menu items
# can use lambda functions to change text of options as well :)
tools_menu_items = [
    SubmenuItem(
        POINTS_DIRECTORY_TOOLS_MENU_DESCRIPTION.title,
        points_directory_tools_menu,
        tools_menu,
    ),
]

add_items_to_menu(tools_menu, tools_menu_items)
