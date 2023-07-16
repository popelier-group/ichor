from typing import Iterable, List

from consolemenu import ConsoleMenu as OriginalConsoleMenu
from consolemenu.items import MenuItem
from consolemenu.screen import Screen as OriginalScreen
from ichor.cli.completers.tab_completer import DoNothingCompleter
from ichor.cli.menu_options import MenuOptions

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
    :param kwargs: Key word arguments to be passed to the original `ConsoleMenu` class.
    """

    def __init__(
        self,
        this_menu_options: MenuOptions = None,
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
        for p_options in self.parent_menu_options:
            # the __call__ method of a MenuOption just makes it into a string which can be printed to the prologue
            prologue_txt += p_options()
        # finally add any new options from the current menu, again __call__ method of MenuOption is used
        if self.this_menu_options:
            prologue_txt += self.this_menu_options()

        return prologue_txt


def add_items_to_menu(menu: ConsoleMenu, items: Iterable[MenuItem]):
    """Adds a list of `MenuItem` instances to a `ConsoleMenu` instance."""

    for i in items:
        menu.append_item(i)
