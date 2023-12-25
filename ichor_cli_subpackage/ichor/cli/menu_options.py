import os
from dataclasses import asdict, dataclass

try:
    from termcolor import colored

    TERMCOLOR_IMPORTED = True
except ImportError:
    TERMCOLOR_IMPORTED = False

# do this on Windows to get the color working
if os.name == "nt":
    os.system("color")


@dataclass
class MenuOptions:
    """Base class for Menu options. Each menu can implements its own options. Formats
    and prints out the options, as well as displays warnings to prologue when there are warnings
    for the given options. These options can be changed by the user."""

    # TODO: use the formatter class
    @staticmethod
    def formatter_menu_options(s: str):
        """Formats the names of the dataclass variables, so they are printed nicely in the terminal."""
        return s.replace("_", " ").capitalize()

    @staticmethod
    def formatter_check_function(s):
        """Formats the string output of the check function, so that the user knows something is wrong."""
        if TERMCOLOR_IMPORTED:
            return colored(f"! {s}", "red")
        return "! " + s

    def run_check_functions(self):
        """Runs all methods that start with `check`.
        These are methods that make sure the current selected values make sense.
        If they do not, warnings are displayed (when warnings are implemented)."""
        all_warnings = []

        # loop over all attribute names
        for attr_name in dir(self):
            # get the actual attribute
            attr = getattr(self, attr_name)
            # if it is a function/method
            if callable(attr):
                # if the name of the function/method starts with check, then we run the function/method
                if attr.__name__.startswith("check"):
                    res = attr()
                    # if there is some result, i.e. function returns
                    # something other than None (a non empty string for example)
                    if res:
                        all_warnings.append(MenuOptions.formatter_check_function(res))

        return all_warnings

    def __str__(self):
        """Format all the defined attributes (which are current menu settings)
        into a nice string to be displayed in the prologue."""
        # k is name of attribute (str), value is value of attribute defined in the dataclass.
        if TERMCOLOR_IMPORTED:
            return "".join(
                [
                    f"-- {MenuOptions.formatter_menu_options(k)}: {colored(str(v), 'green')}\n"
                    for k, v in asdict(self).items()
                ]
            )
        return "".join(
            [
                f"-- {MenuOptions.formatter_menu_options(k)}: {v}\n"
                for k, v in asdict(self).items()
            ]
        )

    def __call__(self):
        """When instance of prologue is called, makes the prologue nicely formatted."""
        attributes_str = str(self)
        warnings = self.run_check_functions()
        # if not an empty list
        if warnings:
            warnings = "\n".join(warnings)
            return attributes_str + "\n\nWarnings:\n" + warnings
        return attributes_str
