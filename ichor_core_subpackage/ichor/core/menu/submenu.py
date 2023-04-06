from pathlib import Path
from typing import Any, Sequence

from ichor.core.common.os import input_with_prefill
from ichor.core.common.types.itypes import Scalar, T
from ichor.core.menu.menu import make_title, MenuVar
from ichor.core.menu.simple_term_menu import TerminalMenu

# todo: document


def toggle_bool_var(bool_var: MenuVar[bool]):
    bool_var.var = not bool_var.var


def set_path_var(path_var: MenuVar[Path], prompt: str = "Enter Path"):
    from ichor.core.analysis.get_path import get_path

    path_var.var = get_path(prompt=prompt, prefill=str(path_var.var))


def choose_dir_var(dir_var: MenuVar[Path], prompt: str = "Enter Directory"):
    from ichor.core.analysis.get_path import get_dir

    print(prompt)
    dir_var.var = get_dir()


def return_arg(arg: T) -> T:
    return arg


def select_multiple_from_list(
    items: Sequence[T],
    result: MenuVar[Sequence[T]],
    title="Select Items",
    empty_ok=False,
):
    menu = TerminalMenu(
        items,
        title=make_title(title),
        multi_select=True,
        clear_screen=True,
        show_multi_select_hint=True,
        multi_select_empty_ok=empty_ok,
        preselected_entries=result.var,
        multi_select_select_on_accept=False,
    )
    menu.show()
    menu_result = menu.chosen_menu_entries
    if len(menu_result) > 0:
        result.var = type(result.var)(map(type(menu_result[0]), menu_result))
    else:
        result.var = type(result.var)()


def set_number(n: MenuVar[Scalar]):
    while True:
        try:
            n.var = type(n.var)(
                input_with_prefill(f"Enter {n.name}: ", prefill=f"{n.var}")
            )
            break
        except ValueError:
            print(f"{n.name} must be of type '{type(n.var)}'")
