import os
from pathlib import Path
from typing import Any, List, Sequence

from ichor.core.common.os import input_with_prefill
from ichor.core.itypes import Scalar, T
from ichor.core.menu.menu import MenuVar, make_title
from ichor.core.menu.tab_completer import ListCompleter

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


def select_multiple_from_list_posix(
    items: Sequence[T],
    result: MenuVar[Sequence[T]],
    title="Select Items",
    empty_ok=False,
):
    from ichor.core.menu.simple_term_menu import TerminalMenu

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


def select_multiple_from_list_compatability(
    items: List[T],
    result: MenuVar[List[T]],
    title: str = "Select Items",
    empty_ok: bool = False,
):
    exit_menu = False
    while not exit_menu:
        print(title)
        print()
        for item in items:
            print(f"[{'x' if item in result.var else ' '}] {item}")
        print()
        with ListCompleter(items):
            while True:
                ans = input(">> ")
                if ans == "all":
                    result.var = list(items)
                    break
                elif ans == "clear":
                    result.var = []
                    break
                elif ans in items:
                    if ans in result.var:
                        del result.var[result.var.index(ans)]
                    else:
                        result.var.append(ans)
                elif ans.strip() == "" or ans == "exit":
                    if not empty_ok and len(result.var) == 0:
                        print("Result cannot be empty")
                    else:
                        exit_menu = True
                        break


select_multiple_from_list = (
    select_multiple_from_list_compatability
    if os.name == "nt"
    else select_multiple_from_list_posix
)


def set_number(n: MenuVar[Scalar]):
    while True:
        try:
            n.var = type(n.var)(
                input_with_prefill(f"Enter {n.name}: ", prefill=f"{n.var}")
            )
            break
        except ValueError:
            print(f"{n.name} must be of type '{type(n.var)}'")
