from typing import Iterable

def add_items_to_menu(menu: "ConsoleMenu", items: Iterable["MenuItem"]):

    for i in items:
        menu.append_item(i)