from pathlib import Path

from ichor.core.common.os import input_with_prefill
from ichor.core.menu import Menu, MenuVar
from ichor.hpc import GLOBALS


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
    with Menu(f"{global_variable} Allowed Values") as menu:
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


def refresh_edit_globals(menu: Menu, global_variable: str):
    menu.update_var("Value", GLOBALS.get(global_variable))
    menu.update_var("Type", GLOBALS.__annotations__[global_variable])
    menu.update_var("Default", GLOBALS._defaults[global_variable])
    menu.update_var("Protected", GLOBALS._defaults[global_variable])
    menu.update_var(
        "Changed",
        GLOBALS.get(global_variable) != GLOBALS._defaults[global_variable],
    )


def edit_global(global_variable: str) -> None:
    with Menu(
        f"Edit {global_variable}",
        update=lambda x: refresh_edit_globals(x, global_variable),
    ) as menu:
        menu.add_var(GLOBALS.get(global_variable), "Value")
        menu.add_space()
        menu.add_var(GLOBALS.__annotations__[global_variable], "Type")
        menu.add_var(GLOBALS._defaults[global_variable], "Default")
        menu.add_space()
        menu.add_var(global_variable in GLOBALS._protected, "Protected")
        menu.add_var(
            GLOBALS.get(global_variable) != GLOBALS._defaults[global_variable],
            "Changed",
        )
        menu.add_space()
        menu.add_option(
            "e", "Edit Setting", edit_value, args=[global_variable]
        )
        menu.add_option(
            "d",
            "Revert to Default",
            GLOBALS.set,
            kwargs={
                "name": global_variable,
                "value": GLOBALS._defaults[global_variable],
            },
        )
        if global_variable in GLOBALS._allowed_values.keys():
            menu.add_option(
                "c",
                "Choose from allowed values",
                choose_value,
                args=[global_variable],
            )


def edit_config_location(config_location: MenuVar[Path]):
    print("Enter new config location")
    config_location.var = Path(
        input(">> ")
        if config_location.var is None
        else input_with_prefill(">> ", str(config_location.var))
    )


def update_global_values(menu: Menu):
    for global_variable in GLOBALS.global_variables:
        menu.update_var(global_variable, GLOBALS.get(global_variable))


def settings_menu() -> None:
    from ichor.hpc import GLOBALS

    config_location = MenuVar("Config Location", GLOBALS._config_file)

    with Menu("Options Menu", update=update_global_values) as menu:
        for global_variable in GLOBALS.global_variables:
            menu.add_var(
                GLOBALS.get(global_variable), name=global_variable, hidden=True
            )
        for global_variable in GLOBALS.global_variables:
            menu.add_option(
                f"{global_variable}",
                menu.get_var(global_variable),
                edit_global,
                kwargs={"global_variable": global_variable},
                hidden=global_variable in GLOBALS._protected,
            )
        menu.add_space()
        menu.add_option(
            "e",
            "Edit config file location",
            edit_config_location,
            args=[config_location],
        )
        menu.add_option(
            "s",
            "Save settings to config file",
            GLOBALS.save_to_config,
            args=[config_location],
        )
        menu.add_space()
        menu.add_var(config_location)

    GLOBALS._config_file = config_location.var
