from ichor.arguments import Arguments
from ichor.globals.globals import Globals
from ichor.globals.machine import Machine
from ichor.globals.os import OS
from ichor.menu import Menu

__all__ = ["GLOBALS", "Machine", "OS"]

with Arguments():
    GLOBALS = Globals.define()

def edit_global(global_variable) -> None:
    pass

def settings_menu() -> None:
    global GLOBALS
    with Menu("Options Menu", space=True, back=True, exit=True) as menu:
        for global_variable in GLOBALS.global_variables:
            if global_variable not in GLOBALS._protected:
                menu.add_option(f"{global_variable}", f"{GLOBALS.get(global_variable)}", edit_global, kwargs={"global_variable": global_variable})
