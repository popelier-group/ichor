"""Implements Tab completion for ICHOR's menus. Tab completion
is handy when providing files or browsing between ICHOR menus."""

import os
import signal
import threading
import time
from abc import ABC, abstractmethod

# if readline is not accessible, then we cannot do tab completion
# but we need to handle for this since we do not want ICHOR to crash
try:
    import readline
except ImportError:
    readline = None


# Set while a completer is scanning the filesystem. Used by the SIGINT handler
# installed by `install_completion_interrupt_handler` to tell apart a Ctrl+C
# meant to cancel a slow completion from a Ctrl+C meant to quit ichor.
_completion_in_progress = threading.Event()
# Set by that same handler to ask the running scan to stop early.
_abort_completion = threading.Event()


def install_completion_interrupt_handler() -> None:
    """Makes Ctrl+C cancel an in-progress Tab completion instead of killing ichor.

    The menu loop runs in a (daemon) thread while the main thread is parked in
    `Thread.join`, and Python only ever runs signal handlers on the main thread.
    That means a Ctrl+C pressed while a completer is scanning a slow filesystem
    cannot interrupt the completer at all -- it unwinds the `join` on the main
    thread and takes the whole program down with it.

    This installs a handler which, if a completion is currently running, only
    raises a flag that the scan polls, and otherwise defers to whatever handler
    was in place before (normally `signal.default_int_handler`, i.e. a normal
    `KeyboardInterrupt`). A main thread waiting on a lock wakes up on `EINTR`,
    runs the handler and then carries on waiting, so cancelling a completion
    this way leaves the menu running.

    .. note::
        Must be called from the main thread; it is a no-op anywhere else, and a
        no-op if the `readline` module is unavailable.
    """

    if readline is None:
        return

    try:
        previous_handler = signal.getsignal(signal.SIGINT)
    except (AttributeError, ValueError):
        return

    def handler(signum, frame):
        if _completion_in_progress.is_set():
            _abort_completion.set()
            return
        if callable(previous_handler):
            previous_handler(signum, frame)
        elif previous_handler != signal.SIG_IGN:
            raise KeyboardInterrupt

    try:
        signal.signal(signal.SIGINT, handler)
    except ValueError:
        # not running on the main thread, so a handler cannot be installed
        pass


# todo: move this to core


class TabCompleter(ABC):
    """Abstract method for any kind of auto completion in the user input prompt when pressing Tab."""

    @abstractmethod
    def completer(self, text, state):
        """
        Needs to be implemented by any class inheriting from TabCompleter. This method will
        define what kinds of things are shown with Tab completion.

        :param text: Text that has been typed into the prompt
        :param state: An integer value that is used by the readline package to
            return possible word completions. See readline.set_completer in docs.
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

    def remove_completer(self) -> None:
        """Remove the completer to prevent word completion in a menu."""
        if readline:
            readline.set_completer(None)
            readline.parse_and_bind("tab: insert-tab")

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


# class ListCompleter(TabCompleter):
#     """
#     Used to complete options which are shown in an ICHOR menu.

#     :param list_completions: A list of strings which are the options to be auto completed when the user types
#     in the prompt and presses Tab.
#     """

#     def __init__(self, list_completions: List[str]):
#         self.list_completions = list_completions

#     def completer(self, text, state):
#         if readline:
#             line = (
#                 readline.get_line_buffer()
#             )  # get what is currently typed in the prompt
#             if not line:
#                 return [c + " " for c in self.list_completions][state]
#             else:
#                 return [
#                     c + " "
#                     for c in self.list_completions
#                     if c.startswith(line)
#                 ][state]


class PathCompleter(TabCompleter):
    """
    Used to show the paths to files when the user pressed Tab.

    readline asks for one match at a time, calling `completer` with
    `state` = 0, 1, 2, ... until it returns `None`, so the directory is scanned
    once (on `state` 0) and the matches are cached for the remaining calls.
    Scanning per call instead makes a Tab press cost O(number of entries squared)
    filesystem calls, which is what used to freeze the menu for minutes when
    completing inside directories holding thousands of points, especially on a
    network filesystem.

    The scan is also bounded, so a slow or hanging filesystem degrades to a
    partial (or empty) list of completions rather than a frozen menu:
    `scan_time_budget` caps how long it may run for and `max_matches` caps how
    many entries it collects. It stops early as well if the user presses Ctrl+C,
    provided `install_completion_interrupt_handler` has been called.
    """

    #: seconds a single directory scan is allowed to take before giving up
    scan_time_budget = 2.0
    #: most matches to collect, so a huge directory cannot flood the terminal
    max_matches = 2000

    def __init__(self):
        self._cached_text = None
        self._matches = []

    def completer(self, text, state):
        if not readline:
            return None
        # only touch the filesystem on the first call for a given prompt text
        if state == 0 or text != self._cached_text:
            self._cached_text = text
            self._matches = self._find_matches(text)
        try:
            return self._matches[state]
        except IndexError:
            # readline stops asking for matches once None is returned
            return None

    def _find_matches(self, text):
        """Returns the paths starting with `text`, as typed (i.e. a leading `~`
        is used to find the matches but is kept in what is shown back).

        :param text: Text that has been typed into the prompt
        """

        expanded = os.path.expanduser(text)
        head, separator, prefix = expanded.rpartition(os.sep)
        # keep the separator so that the root directory stays "/" and not ""
        directory = head + separator if separator else "."
        # the part of what the user typed which is not being completed
        typed_directory = text[: len(text) - len(prefix)]
        # only offer hidden files if the user has started typing one
        include_hidden = prefix.startswith(".")

        deadline = time.monotonic() + self.scan_time_budget
        _abort_completion.clear()
        _completion_in_progress.set()
        matches = []
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    if not entry.name.startswith(prefix):
                        continue
                    if entry.name.startswith(".") and not include_hidden:
                        continue
                    # is_dir uses the directory entry type where the operating
                    # system provides it, so this costs no extra system call
                    matches.append(
                        typed_directory
                        + entry.name
                        + (os.sep if entry.is_dir() else "")
                    )
                    if (
                        len(matches) >= self.max_matches
                        or _abort_completion.is_set()
                        or time.monotonic() > deadline
                    ):
                        break
        except OSError:
            # an unreadable, missing or half typed directory is not an error,
            # it just means there is nothing to complete
            return []
        finally:
            _completion_in_progress.clear()
            _abort_completion.clear()

        return sorted(matches)


class DoNothingCompleter(TabCompleter):
    """This completer does not do anything, but fixes
    issues where PathCompleter modifies how the tab button works.

    """

    def completer(self, text, state):
        return super().completer(text, state)

    def setup_completer(self, pattern="\t") -> None:
        """
        If readline package is present, then we can use tab completion.
        :param pattern: Which set of characters to use as delimiter. Default is `\t` which is a Tab
        """
        if readline:
            readline.set_completer_delims(pattern)  # set a tab as delimiter
            readline.parse_and_bind("tab: insert-tab")  # set tab to trigger readline
            readline.set_completer(
                self.completer
            )  # depending on menu, a different functionality is needed for readline

    def remove_completer(self) -> None:
        """Remove the completer to prevent word completion in a menu."""
        if readline:
            readline.set_completer(None)
            readline.parse_and_bind("tab: insert-tab")
