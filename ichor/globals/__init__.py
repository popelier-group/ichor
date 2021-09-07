""" GLOBALS is an instance which holds all important settings information for all programs (ICHOR, Gaussian, AIMALL, Ferebus). It has default options as
defined in globals.py, but these can be overwritten using an ICHOR config file. GLOBALS also determine imporatnt values/keywords depending on the machine (CSF3/FFLUXLAB)
that ICHOR is being ran on."""

from ichor.arguments import Arguments
from ichor.common.os import input_with_prefill
from ichor.globals.globals import Globals
from ichor.globals.os import OS
from ichor.menu import Menu

__all__ = ["GLOBALS", "OS"]

with Arguments():
    GLOBALS = Globals.define()


def edit_value(global_variable):
    print(f"Edit {global_variable}")
    while True:
        new_value = input_with_prefill(">> ", GLOBALS.get(global_variable))
        try:
            GLOBALS.set(global_variable, new_value)
            break
        except TypeError:
            print(
                f"Value Error: Must be of type {GLOBALS.__annotations__[global_variable].__name__}"
            )


def choose_value(global_variable):
    with Menu(
        title=f"{global_variable} Allowed Values",
        auto_close=True,
        space=True,
        back=True,
        exit=True,
    ) as menu:
        for i, allowed_value in enumerate(
            GLOBALS._allowed_values[global_variable]
        ):
            menu.add_option(
                str(i + 1),
                str(allowed_value),
                GLOBALS.set,
                kwargs={"name": global_variable, "value": allowed_value},
            )
            menu.add_option(
                str(allowed_value),
                str(allowed_value),
                GLOBALS.set,
                kwargs={"name": global_variable, "value": allowed_value},
                hidden=True,
            )


def edit_global_refresh(menu) -> None:
    global GLOBALS
    menu.clear_options()
    menu.add_message(f"Value: {GLOBALS.get(_gv)}")
    menu.add_space()
    menu.add_message(f"Type: {GLOBALS.__annotations__[_gv]}")
    menu.add_message(f"Default: {GLOBALS._defaults[_gv]}")
    menu.add_space()
    menu.add_message(f"Protected: {_gv in GLOBALS._protected}")
    menu.add_message(f"Changed: {GLOBALS.get(_gv) != GLOBALS._defaults[_gv]}")
    menu.add_space()
    menu.add_option(
        "e", "Edit Setting", edit_value, kwargs={"global_variable": _gv}
    )
    menu.add_option(
        "d",
        "Revert to Default",
        GLOBALS.set,
        kwargs={"name": _gv, "value": GLOBALS._defaults[_gv]},
    )
    if _gv in GLOBALS._allowed_values.keys():
        menu.add_option(
            "c",
            "Choose from allowed values",
            choose_value,
            kwargs={"global_variable": _gv},
        )
    menu.add_final_options()


def edit_global(global_variable) -> None:
    global _gv
    _gv = global_variable
    with Menu(f"Edit {global_variable}", refresh=edit_global_refresh) as menu:
        pass


def settings_menu_refresh(menu):
    menu.clear_options()
    for global_variable in GLOBALS.global_variables:
        menu.add_option(
            f"{global_variable}",
            f"{GLOBALS.get(global_variable)}",
            edit_global,
            kwargs={"global_variable": global_variable},
            hidden=global_variable in GLOBALS._protected,
        )
    menu.add_final_options()


def settings_menu() -> None:
    global GLOBALS
    with Menu("Options Menu", refresh=settings_menu_refresh) as menu:
        pass
