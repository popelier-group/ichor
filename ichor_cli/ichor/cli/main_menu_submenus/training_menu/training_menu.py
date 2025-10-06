from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
from consolemenu.items import FunctionItem, SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.training_menu.training_submenus.data_preparation_menu import(
    submit_data_prep_menu,
    SUBMIT_DATA_PREP_MENU_DESCRIPTION
)

from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions.user_input import user_input_path


TRAINING_MENU_DESCRIPTION = MenuDescription(
    "Training Menu",
    subtitle="Use this menu to prepare datasets, train and analyse GPR models.\n",
)


training_menu_options = [""]

# initialize menu
training_menu = ConsoleMenu(
    this_menu_options=training_menu_options,
    title=TRAINING_MENU_DESCRIPTION.title,
    subtitle=TRAINING_MENU_DESCRIPTION.subtitle,
    prologue_text=TRAINING_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=TRAINING_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=TRAINING_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
training_menu_items = [
    SubmenuItem(
        SUBMIT_DATA_PREP_MENU_DESCRIPTION.title,
        submit_data_prep_menu,
        training_menu,
    ),
]

add_items_to_menu(training_menu, training_menu_items)
