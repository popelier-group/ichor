import os
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from termcolor import colored

    TERMCOLOR_IMPORTED = True
except ImportError:
    TERMCOLOR_IMPORTED = False

# do this on Windows to get the color working
if os.name == "nt":
    os.system("color")


def shorten_path_for_display(value, keep_start: int = 2, keep_end: int = 2) -> str:
    """Shortens a long path for display so that the menu prologue fits on one screen.

    The first ``keep_start`` and last ``keep_end`` named path components are kept (any
    leading root/drive is preserved) and the middle is replaced with ``...``
    (e.g. ``/mnt/iusers01/pp01/user/DL_FFLUX/RUN0`` becomes
    ``/mnt/iusers01/.../DL_FFLUX/RUN0``). Paths that are already short enough are
    returned unchanged.

    :param value: The path (``Path`` or path-like string) to shorten.
    :param keep_start: The number of leading named path components to keep.
    :param keep_end: The number of trailing named path components to keep.
    """
    p = Path(value)
    anchor = p.anchor  # e.g. "/" (posix) or "C:\\" (windows), "" if relative
    # named components, excluding any leading root/drive anchor
    named = [part for part in p.parts if part != anchor]
    if len(named) <= keep_start + keep_end:
        return str(value)
    sep = "\\" if ("\\" in anchor or "\\" in str(value)) else "/"
    start = sep.join(named[:keep_start])
    end = sep.join(named[-keep_end:])
    return f"{anchor}{start}{sep}...{sep}{end}"


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

    def get_display_value(self, value):
        """Formats a single option value for display in the prologue. Long paths (and
        path-like strings) are shortened so the menu fits on one screen; all other
        values are displayed unchanged. Subclasses can override this for custom display."""
        if isinstance(value, Path):
            return shorten_path_for_display(value)
        if isinstance(value, str) and ("/" in value or "\\" in value):
            return shorten_path_for_display(value)
        return value

    @staticmethod
    def formatter_check_function(s):
        """Formats the string output of the check function, so that the user knows something is wrong."""
        if TERMCOLOR_IMPORTED:
            return colored(f"! {s}", "red")
        return "! " + s + "\n"

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
                    f"-- {MenuOptions.formatter_menu_options(k)}: "
                    f"{colored(str(self.get_display_value(v)) if hasattr(self, 'get_display_value') else str(v), 'green')}\n"
                    for k, v in asdict(self).items()
                ]
            )

        return "".join(
            [
                f"-- {MenuOptions.formatter_menu_options(k)}: "
                f"{self.get_display_value(v) if hasattr(self, 'get_display_value') else v}\n"
                for k, v in asdict(self).items()
            ]
        )

    def __call__(self):
        """When instance of prologue is called, makes the prologue nicely formatted."""
        attributes_str = str(self)
        warnings = self.run_check_functions()

        # if there are warnings, make into string
        if warnings:

            warnings = "\n".join(warnings)
            warnings += "\n"

        else:
            warnings = ""

        if TERMCOLOR_IMPORTED:

            if warnings:

                return (
                    attributes_str
                    + "\n\n"
                    + colored("Warnings:", "red")
                    + "\n"
                    + warnings
                )

            else:

                return attributes_str

        else:

            if warnings:
                return attributes_str + "\n\nWarnings:\n" + warnings

            return attributes_str
