"""Implements Tab completion for ICHOR's menus. Tab completion is handy when providing files or browsing between ICHOR menus."""

import os
from abc import ABC, abstractmethod
from glob import glob
from pathlib import Path

try:
    import readline
except ImportError:
    readline = None


class TabCompleter(ABC):
    @abstractmethod
    def completer(self, text, state):
        pass

    def setup_completer(self, pattern="\t"):
        if readline:
            readline.set_completer_delims(pattern)
            readline.parse_and_bind("tab: complete")
            readline.set_completer(self.completer)

    @staticmethod
    def remove_completer():
        if readline:
            readline.set_completer(None)

    def __enter__(self):
        self.setup_completer()

    def __exit__(self, type, value, traceback):
        self.remove_completer()


class ListCompleter(TabCompleter):
    def __init__(self, list_completions):
        self.list_completions = list_completions

    def completer(self, text, state):
        if readline:
            line = readline.get_line_buffer()
            if not line:
                return [c + " " for c in self.list_completions][state]
            else:
                return [
                    c + " "
                    for c in self.list_completions
                    if c.startswith(line)
                ][state]


class PathCompleter(TabCompleter):
    def completer(self, text, state):
        if not readline:
            return
        p = Path(text)
        if "~" in text:
            p = p.expanduser()
        p = f"{p}{os.sep if p.is_dir() else ''}"  # Add trailing slash if p is a directory
        if p == f".{os.sep}":
            p = ""  # No point in showing ./

        files = [x for x in glob(p + "*")]
        for i, f in enumerate(files):
            if Path(f).is_dir():
                files[i] += os.sep
        return files[state]
