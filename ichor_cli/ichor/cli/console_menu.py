from typing import Callable, Dict, Iterable, List, NamedTuple

from consolemenu import ConsoleMenu as OriginalConsoleMenu
from consolemenu.items import MenuItem
from consolemenu.screen import Screen as OriginalScreen
from ichor.cli.completers.tab_completer import DoNothingCompleter
from ichor.cli.menu_options import MenuOptions

# from consolemenu.menu_formatter import MenuFormatBuilder
# from consolemenu.menu_component import Dimension

# TODO: maybe imporve screen size
# TODO: also maybe find a better way to fix the slight bug with user input
# import shutil


class Screen(OriginalScreen):
    """Screen size of menu, overwrites some methods from library class."""

    def __init__(self):
        # self.__height, self.__width = shutil.get_terminal_size()
        self.__height = 100
        self.__width = 100

    def input(self, prompt: str = ""):
        """
        Prompt the end user for input.
        Without overwriting this, pressing Tab makes a tab.
        However, PathCompleter changes this, so after using a function with PathCompleter,
        the Tab button no longer makes a tab. With this fix, pressing Tab
        in any selection menu does not do anything (i.e. does not insert a tab like it did before).
        Menus requiring PathCompleter still work as intended and paths are auto-completed.

        :param prompt: The message to display as the prompt.
        :returns: The input provided by the user.
        """
        with DoNothingCompleter():
            return input(prompt)


class GlobalShortcut(NamedTuple):
    """A menu that can be opened from every other menu by typing one key."""

    text: str
    # a function returning the menu, so that the module registering the shortcut does
    # not have to be imported by this one
    get_menu: Callable[[], "ConsoleMenu"]


# key typed at any menu's ">>" prompt -> the menu it opens
GLOBAL_SHORTCUTS: Dict[str, GlobalShortcut] = {}


def register_global_shortcut(
    key: str, text: str, get_menu: Callable[[], "ConsoleMenu"]
):
    """Makes a menu openable from every menu by typing ``key``, e.g. the job submission
    options, which are wanted just before submitting from whichever menu that is.

    :param key: A single letter, which must not be one a menu uses for an item (the
        exit item uses ``q``).
    :param text: What the menu is called in the hint shown under every menu.
    :param get_menu: Returns the menu to open.
    """

    GLOBAL_SHORTCUTS[key.lower()] = GlobalShortcut(text, get_menu)


class ConsoleMenu(OriginalConsoleMenu):
    """Subclasses from `consolemenu.ConsoleMenu`, which is the base menu class. This subclass
    adds the `this_menu_options` attribute, which contains options for the menus,
    see the `MenuOptions` class. These options can be changed.

    Also, the `get_prologue_text` method is overwritten here to be able print out extra info
    in the prologue before the menu items. The information printed is stored variables (that the
    user has selected) as well as any warnings. Since menus can open submenus, the submenus get the
    options of the parent menus, and the submenus can also add their own options.

    For example the pointsdirectory menu can be used to select a folder which is in the structure
    of a `PointsDirectory`. Then a submenu can be used and it will remember the chosen folder in the parent
    directory. Also, this submenu can put in its own options (which will be displayed in the prolog
    along with the parent options and any warnings).

    :param this_menu_options: A `MenuOptions` instance (a dataclass) containing options which can be
        changed by the user.
    :param show_parent_options: Whether the options of the menus above this one are shown in its
        prologue. A menu that can be opened from anywhere (see `register_global_shortcut`) has
        nothing to do with the menu it was opened from, so it turns this off.
    :param kwargs: Key word arguments to be passed to the original `ConsoleMenu` class.
    """

    def __init__(
        self,
        this_menu_options: MenuOptions = None,
        show_parent_options: bool = True,
        title=None,
        subtitle=None,
        # screen=None,
        formatter=None,
        prologue_text=None,
        epilogue_text=None,
        clear_screen=True,
        show_exit_option=True,
        exit_option_text="Exit",
        exit_menu_char="q",
    ):

        # make screen bigger by default
        # if screen is None:
        #     screen = Screen()
        # self.screen = screen

        super().__init__(
            title=title,
            subtitle=subtitle,
            screen=Screen(),  # always overwrite the screen with our Screen class
            formatter=formatter,
            prologue_text=prologue_text,
            epilogue_text=epilogue_text,
            clear_screen=clear_screen,
            show_exit_option=show_exit_option,
            exit_option_text=exit_option_text,
            exit_menu_char=exit_menu_char,
        )

        self.this_menu_options = this_menu_options
        self.show_parent_options = show_parent_options
        # the ">>" prompt, taken out of the drawn menu by `draw` so that it can be
        # handed to `input` by `get_input` instead (see those methods)
        self._input_prompt = ""
        # if formatter is None:
        #     formatter = MenuFormatBuilder(max_dimension=Dimension(120, 100))
        # self.formatter = formatter

    def draw(self):
        """Draws the menu, but stops just short of the trailing `">>"` prompt, which is
        kept back in `self._input_prompt` for `get_input` to pass to `input`.

        The library prints the prompt as the last (newline-less) part of the formatted
        menu and then calls `input()` with an empty prompt string. `readline` therefore
        thinks the line it is editing starts at the left edge of the terminal, and since
        every redisplay (a Backspace, an arrow key, a completion) begins by returning the
        cursor to that edge, it draws what has been typed over the `">>"` and the prompt
        disappears. Giving the prompt to `input` instead tells `readline` how many columns
        to leave alone, so the prompt survives editing.
        """

        formatted_menu = self.formatter.format(
            title=self.get_title(),
            subtitle=self.get_subtitle(),
            items=self.items,
            prologue_text=self.get_prologue_text(),
            epilogue_text=self.get_epilogue_text(),
        )
        # everything after the last newline is the prompt, as the section before it
        # (the menu footer) is newline terminated but the prompt itself is not
        menu_without_prompt, newline, prompt = formatted_menu.rpartition("\n")
        self._input_prompt = prompt
        self.screen.printf(menu_without_prompt + newline)

    def get_input(self):
        """Prompts for the menu selection, using the prompt that `draw` held back."""

        return self.screen.input(self._input_prompt)

    def _shortcuts_available_here(self) -> Dict[str, GlobalShortcut]:
        """The global shortcuts that open a menu other than this one."""

        return {
            key: shortcut
            for key, shortcut in GLOBAL_SHORTCUTS.items()
            if shortcut.get_menu() is not self
        }

    def get_epilogue_text(self) -> str:
        """The menu's own epilogue, followed by a hint for each global shortcut, so that
        they can be found from whichever menu the user is in."""

        epilogue = super().get_epilogue_text() or ""
        hints = [
            f"Press {key} for {shortcut.text}"
            for key, shortcut in self._shortcuts_available_here().items()
        ]
        if not hints:
            return epilogue

        return (epilogue + "\n" if epilogue else "") + "\n".join(hints)

    def process_user_input(self):
        """Handles the selection as the library does, apart from the keys registered with
        `register_global_shortcut`, which open their menu on top of this one."""

        try:
            user_input = self.get_input()
        except EOFError:
            self.should_exit = True
            return

        shortcut = self._shortcuts_available_here().get(user_input.strip().lower())
        # a key a menu item claims for itself keeps meaning that item
        claimed = any(item.menu_char == user_input for item in self.items)
        if shortcut is not None and not claimed:
            self.open_on_top(shortcut.get_menu())
            return user_input

        # the rest is the library's own handling of the input
        for i, item in enumerate(self.items):
            if item.menu_char == user_input:
                self.current_option = i
                self.select()
                return user_input

        try:
            num = int(user_input)
        except ValueError:
            return
        if 0 < num < len(self.items) + 1:
            self.current_option = num - 1
            self.select()

        return user_input

    def open_on_top(self, menu: "ConsoleMenu"):
        """Opens a menu as though it were a submenu of this one, the way `SubmenuItem`
        does, and puts it back as it was once it is closed.

        The menu may already be the submenu of another menu (the main menu lists the job
        submission options too), so its parent is only borrowed while it is open.
        Otherwise its exit item would say "Return to" whichever menu last opened it.
        """

        previous_parent = menu.parent
        menu.parent = self
        # the exit item works out its "Return to ..." text from the parent, but only
        # while its text is still the default
        menu.exit_item.text = "Exit"

        self.pause()
        self.clear_screen()
        try:
            menu.start()
            menu.join()
        finally:
            menu.parent = previous_parent
            menu.exit_item.text = "Exit"
            self.clear_screen()
            self.resume()

    @property
    def parent_menu_options(self) -> List[MenuOptions]:
        """Returns a list of `MenuOption` instances which contain information about options
        from parent classes. The list is reverse sorted, meaning that the earliest class is displayed
        first."""

        # list with "MenuOptions" of all parent classes
        # from all menus that are parents to this menu
        _parent_menu_options = []

        prnt = self.parent
        # while there is a parent menu, get the MenuOptions for the parent
        while prnt is not None:
            _parent_menu_options.append(prnt.this_menu_options)
            # move to "upper" parent
            prnt = prnt.parent

        # reverse ordering so that oldest parent options are at the top
        _parent_menu_options = _parent_menu_options[::-1]
        return _parent_menu_options

    def get_prologue_text(self) -> str:
        """Gets the prologue text, containing information for saved variables that are needed for jobs.
        First, if the `ConsoleMenu` instance has a default `self.prologue_text`, this gets printed out (this
        should not really be needed, can put this info in the subtitle anyway).
        After that, the information of options from parent classes is printed out (the oldest parent options
        are at the top).
        Finally, any options that the current menu adds are printed.
        """

        # if there is some constant prologue text to be displayed for some menu for some reason
        # there really shouldn't be a need for this but keep for now
        prologue_txt = (
            self.prologue_text() if callable(self.prologue_text) else self.prologue_text
        )
        # add the strings that each parent gives
        parent_menu_options = (
            self.parent_menu_options if self.show_parent_options else []
        )
        for p_options in parent_menu_options:
            # a parent menu may not define any options (this_menu_options is None), e.g. the
            # Analysis menu; skip those so we don't call None()
            if p_options is None:
                continue
            # the __call__ method of a MenuOption just makes it into a string which can be printed to the prologue
            # (a parent menu may have no options, i.e. this_menu_options is None, so guard against that)
            if p_options:
                prologue_txt += p_options()
        # finally add any new options from the current menu, again __call__ method of MenuOption is used
        if self.this_menu_options:
            prologue_txt += self.this_menu_options()

        return prologue_txt


def add_items_to_menu(menu: ConsoleMenu, items: Iterable[MenuItem]):
    """Adds a list of `MenuItem` instances to a `ConsoleMenu` instance."""

    for i in items:
        menu.append_item(i)
