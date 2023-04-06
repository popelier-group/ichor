"""Implements Tab completion for ICHOR's menus. Tab completion is handy when providing files or browsing between ICHOR menus."""

import os
from abc import ABC, abstractmethod
from glob import glob
from pathlib import Path
from typing import List

# if readline is not accessible, then we cannot do tab completion
# but we need to handle for this since we do not want ICHOR to crash
try:
    import readline
except ImportError:
    readline = None


# todo: move this to core


class TabCompleter(ABC):
    """Abstract method for any kind of auto completion in the user input prompt when pressing Tab."""

    @abstractmethod
    def completer(self, text, state):
        """
        Needs to be implemented by any class inheriting from TabCompleter. This method will
        define what kinds of things are shown with Tab completion.

        :param text: Text that has been typed into the prompt
        :param state: An integer value that is used by the readline package to return possible word completions. See readline.set_completer in docs.
        """
        pass

    def setup_completer(self, pattern="\t") -> None:
        """
        If readline package is present, then we can use tab completion.
        :param pattern: Which set of characters to use as delimiter. Default is `\t` which is a Tab
        """
        if readline:
            readline.set_completer_delims(pattern)  # set a tab as delimiter
            readline.parse_and_bind("tab: complete")  # set tab to trigger readline
            readline.set_completer(
                self.completer
            )  # depending on menu, a different functionality is needed for readline

    @staticmethod
    def remove_completer() -> None:
        """Remove the completer to prevent word completion in a menu."""
        if readline:
            readline.set_completer(None)

    def __enter__(self):
        """
        Executed the `setup_completer` method.
        To be used in when entering a `with` context manager. This way, word completion can be implemented as
        `with ListCompleter(self.get_options()):` or `with PathCompleter(self.get_options()):`
        """
        self.setup_completer()

    def __exit__(self, type, value, traceback):
        """
        Executes the `remove_completer` method automatically when the `with` block is exited.
        """
        self.remove_completer()


class ListCompleter(TabCompleter):
    """
    Used to complete options which are shown in an ICHOR menu.

    :param list_completions: A list of strings which are the options to be auto completed when the user types
    in the prompt and presses Tab.
    """

    def __init__(self, list_completions: List[str]):
        self.list_completions = list_completions

    def completer(self, text, state):
        if readline:
            line = (
                readline.get_line_buffer()
            )  # get what is currently typed in the prompt
            if not line:
                return [c + " " for c in self.list_completions][state]
            else:
                return [c + " " for c in self.list_completions if c.startswith(line)][
                    state
                ]


class PathCompleter(TabCompleter):
    """
    Used to show the paths to files when the user pressed Tab.
    """

    def completer(self, text, state):
        if not readline:
            return
        p = Path(text)
        if (
            "~" in text
        ):  # if home directory is shown as ~/ show the full path from /home/ instead
            p = p.expanduser()
        p = f"{p}{os.sep if p.is_dir() else ''}"  # Add trailing slash if p is a directory
        if p == f".{os.sep}":
            p = ""  # No point in showing ./

        files = [
            x for x in glob(p + "*")
        ]  # find all files which match what is typed into the prompt
        for i, f in enumerate(files):
            if Path(f).is_dir():
                files[i] += os.sep
        return files[state]
