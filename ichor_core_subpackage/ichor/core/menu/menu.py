import sys
from abc import ABC, abstractmethod
from collections import namedtuple
from typing import Any, Callable, Dict, Generic, List, Optional, Union

from ichor.core.common.os import clear_screen
from ichor.core.itypes import F, T
from ichor.core.menu.tab_completer import ListCompleter


# TODO: why use a namedtuple?, also return_val and close need to be in a list. This would not work like it is now.
# TODO: add problem messages
OptionReturn = namedtuple("OptionReturn", "return_val close")

class MenuItem(ABC):
    def __init__(self, name: str, hidden: bool = False):
        self.name = name
        self.hidden = hidden

    @abstractmethod
    def __repr__(self):
        pass

class MenuOption(MenuItem):
    def __init__(
        self,
        label: str,
        name: Union[str, "MenuVar"],
        func: F,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        hidden: bool = False,
        wait: bool = False,
        auto_close: bool = False,
        replace_vars: bool = True,
        debug: bool = False,
    ):
        args = args or []
        kwargs = kwargs or {}
        super().__init__(name, hidden)
        self.label = label
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.wait = wait
        self.auto_close = auto_close

        self._replace_vars = replace_vars
        self._debug = debug

    def select(self) -> OptionReturn:
        # Below args and kwargs unwraps instances of MenuVar with the MenuVar.var based upon function annotations
        args = [
            arg.var
            if isinstance(arg, MenuVar)
            or not hasattr(self.func, "__annotations__")
            or (
                len(self.func.__annotations__) > i
                and hasattr(
                    list(self.func.__annotations__.values())[i],
                    "__origin__",
                )
                and list(self.func.__annotations__.values())[i].__origin__
                is not MenuVar
            )
            else arg
            for i, arg in enumerate(self.args)
        ]
        kwargs = {
            key: val.var
            if isinstance(val, MenuVar)
            or not hasattr(self.func, "__annotations__")
            or (
                key in self.func.__annotations__.keys()
                and hasattr(self.func.__annotations__[key], "__origin__")
                and self.func.__annotations__[key].__origin__ is not MenuVar
            )
            else val
            for key, val in self.kwargs.items()
        }
        option_return = OptionReturn(
            self.func(*args, **kwargs), self.auto_close
        )
        if self.wait:
            input("[Return]")
        return option_return

    def __repr__(self):
        name = self.name.var if isinstance(self.name, MenuVar) else self.name
        return f"[{self.label}] {name}"

class MenuMessage(MenuItem):
    def __init__(self, name, message, hidden: bool = False):
        super().__init__(name, hidden)
        self.message = message

    def __repr__(self):
        return self.message

class MenuVar(MenuMessage, Generic[T]):
    def __init__(
        self,
        message: str,
        var: T,
        name: str = "__var__",
        hidden: bool = False,
        custom_formatter: Optional[Callable[[Any], str]] = None,
    ):
        super().__init__(name, message, hidden=hidden)
        self.var: T = var
        self.custom_formatter = custom_formatter

    def __repr__(self):
        var = (
            self.var
            if self.custom_formatter is None
            else self.custom_formatter(self.var)
        )
        return f"{self.message}: {var}"

class MenuBlank(MenuMessage):
    def __init__(self):
        super().__init__("__blank__", "")

class OptionInMenuError(Exception):
    pass

class OptionNotFoundError(Exception):
    pass

class Menu:
    def __init__(
        self,
        title: str,
        items: Optional[List[MenuItem]] = None,
        prompt: str = ">>",
        blank: bool = True,
        back: bool = True,
        exit: bool = True,
        update: Optional[Callable[["Menu"], None]] = None,
    ):
        self._title = title
        self._prompt = prompt
        self._items: List[MenuItem] = items or []
        self._close = False

        self.blank = blank
        self.back = back
        self.exit = exit

        self._update = update
        self._added_final_options = False

    @property
    def _menu_options(self) -> List[MenuOption]:
        return [item for item in self._items if isinstance(item, MenuOption)]

    @property
    def option_labels(self) -> List[str]:
        return [option.label for option in self._menu_options]

    def add_option(
        self,
        label: str,
        name: Union[str, MenuVar],
        func: F,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        wait: bool = False,
        auto_close: bool = False,
        hidden: bool = False,
        replace_vars: bool = True,
        debug: bool = False,
        overwrite_existing: bool = False,
    ):
        if label in self.option_labels and not overwrite_existing:
            raise OptionInMenuError(
                f"'{label}' already an option in '{self._title}' instance of '{self.__class__.__name__}'"
            )
        self._items.append(
            MenuOption(
                label,
                name,
                func,
                args,
                kwargs,
                hidden=hidden,
                wait=wait,
                auto_close=auto_close,
                replace_vars=replace_vars,
                debug=debug,
            )
        )

    def add_message(self, message: str, name: Optional[str] = None):
        name = name or "__message__"
        self._items.append(MenuMessage(name, message))

    def add_var(
        self,
        var: Union[MenuVar, Any],
        name: Optional[str] = None,
        hidden: bool = False,
    ):
        if isinstance(var, MenuVar):
            var.hidden = hidden
            self._items.append(var)
        else:
            name = name or "<Insert Name>"
            self._items.append(MenuVar(name, var, name=name, hidden=hidden))

    def add_space(self):
        self.add_blank()

    def add_blank(self):
        self._items.append(MenuBlank())

    def add_back(self):
        self.add_option("b", "Back", func=self.close)

    def add_exit(self):
        self.add_option("0", "Exit", func=sys.exit)

    def add_final_options(
        self, blank: bool = True, back: bool = True, exit: bool = True
    ):
        if not self._added_final_options:
            if blank:
                self.add_blank()
            if back:
                self.add_back()
            if exit:
                self.add_exit()
        self._added_final_options = True

    def select(self, label) -> OptionReturn:
        for option in self._menu_options:
            if option.label == label:
                return option.select()
        raise OptionNotFoundError(
            f"'{label}' not found in '{self._title}' instance of '{self.__class__.__name__}'"
        )

    def get_var(self, name: str) -> MenuVar:
        for item in self._items:
            if isinstance(item, MenuVar) and item.name == name:
                return item
        raise ValueError(
            f"No such variable '{name}' in '{self._title}' instance of '{self.__class__.__name__}'"
        )

    def update_var(self, name: str, val: Any):
        self.get_var(name).var = val

    def make_title(self, title: str, title_char: str = "#") -> str:
        char_line = title_char * (len(title) + 2 * len(title_char) + 2)
        title_line = f"{title_char} {title} {title_char}"
        return f"{char_line}\n{title_line}\n{char_line}\n"

    def show(self):
        clear_screen()
        print(self.make_title(self._title))
        for item in self._items:
            if not item.hidden:
                print(item)
        print()

    def close(self):
        self._close = True

    def run(self):
        return_val = None
        while not self._close:
            if self._update is not None:
                self._update(self)
            self.show()
            while True:
                with ListCompleter(self.option_labels):
                    ans = input(f"{self._prompt} ").strip()
                if ans not in self.option_labels:
                    print("Input Error")
                else:
                    option_return = self.select(ans)
                    return_val = option_return.return_val
                    if option_return.close:
                        self._close = option_return.close
                    break
        return return_val

    def __enter__(self):
        """
        To be used when a Menu is constructed as a context manager. Returns the instance of a menu.
        For example, in main_menu.py; `with Menu(f"{path} Menu", space=True, back=True, exit=True) as menu:`
        is used where `with Menu(f"{path} Menu", space=True, back=True, exit=True)` is going to make a new
        instance of class `Menu` which is going to be stored in the variable `menu`. Then, this `menu`
        object can be manipulated (i.e. can have options added to it) inside the `with` block. Using a context
        manager for the menu saves some lines of code when constructing new menus.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Once the `menu`'s `with` context manager block ends, this `__exit__ method is automatically called. It adds
        options to navigate to other menus as well as to exit ICHOR. Finally, the menu's `run` method is called, which
        prints out the menu to the terminal with the options that the user can select from."""
        if exc_type:
            raise exc_type(exc_val)
        if any([self.blank, self.back, self.exit]):
            self.add_final_options(self.blank, self.back, self.exit)
        return self.run()
