"""Main menu that pops up when you run python ICHOR.py (specifically python3 ICHOR.py)"""

import os
import sys
from typing import Callable, List
from uuid import uuid4

from ichor.problem_finder import ProblemFinder
from ichor.tab_completer import ListCompleter


class Menu(object):
    def __init__(
        self,
        title: str = None,
        options: List = None,
        message: str = None,
        prompt: str = ">>",
        refresh: Callable = lambda *args: None,
        auto_clear: bool = True,
        enable_problems: bool = False,
        auto_close: bool = False,
        space=False,
        back=False,
        exit=False,
    ):
        self.title = title
        self.options = None
        if options is None:
            options = []
        self.set_options(options)
        self.is_title_enabled = title is not None
        self.message = message
        self.is_message_enabled = message is not None
        self.refresh = None
        self.set_refresh(refresh)
        self.prompt = prompt
        self.is_open = None
        self.auto_clear = auto_clear
        self.auto_close = auto_close
        self.problems_enabled = enable_problems

        self.gap_ids = []
        self.message_ids = []
        self.wait_options = []
        self.close_options = []
        self.hidden_options = []

        self.space = space
        self.back = back
        self.exit = exit

    def set_options(self, options):
        original = self.options
        self.options = {}
        try:
            for option in options:
                if not isinstance(option, tuple):
                    raise TypeError(option, "option is not a tuple")
                if len(option) < 2:
                    raise ValueError(option, "option is missing a handler")
                kwargs = option[3] if len(option) == 3 else {}
                self.add_option(option[0], option[1], kwargs)
        except (TypeError, ValueError) as e:
            self.options = original
            raise e

    def set_title(self, title):
        self.title = title

    def set_title_enabled(self, is_enabled):
        self.is_title_enabled = is_enabled

    def set_message(self, message):
        self.message = message

    def set_message_enabled(self, is_enabled):
        self.is_message_enabled = is_enabled

    def set_prompt(self, prompt):
        self.prompt = prompt

    def set_refresh(self, refresh):
        if not callable(refresh):
            raise TypeError(refresh, "refresh is not callable")
        self.refresh = refresh

    def clear_options(self):
        self.options = None

        self.gap_ids = []
        self.message_ids = []
        self.wait_options = []
        self.close_options = []
        self.hidden_options = []

        self.set_options([])

    def get_options(self, include_hidden=True):
        return [
            label
            for label, option in self.options.items()
            if label not in self.gap_ids
            and label not in self.message_ids
            and (label not in self.hidden_options or include_hidden)
        ]

    def add_option(
        self,
        label,
        name,
        handler,
        kwargs=None,
        wait=False,
        auto_close=False,
        hidden=False,
    ):
        if kwargs is None:
            kwargs = {}
        if not callable(handler):
            raise TypeError(handler, "handler is not callable")
        self.options[label] = (name, handler, kwargs)
        if wait:
            self.wait_options.append(label)
        if auto_close:
            self.close_options.append(label)
        if hidden:
            self.hidden_options.append(label)

    def add_space(self):
        gap_id = uuid4()
        self.gap_ids.append(gap_id)
        self.options[gap_id] = ("", "", {})

    def add_message(self, message, fmt={}):
        message_id = uuid4()
        self.message_ids.append(message_id)
        self.options[message_id] = (message, fmt, {})

    # open the menu
    def run(self):
        self.is_open = True
        while self.is_open:
            self.refresh(self)
            func, wait, close = self.input()
            if func == Menu.CLOSE:
                func = self.close
            print()
            func()
            if close or self.auto_close:
                self.close()
            input("\nContinue... [Return]") if wait else None

    def close(self):
        self.is_open = False

    def print_title(self):
        print("#" * (len(self.title) + 4))
        print("# " + self.title + " #")
        print("#" * (len(self.title) + 4))
        print()

    def print_problems(self):
        problems = ProblemFinder()
        problems.find()
        if len(problems) > 0:
            max_len = UsefulTools.count_digits(len(problems))
            s = "s" if len(problems) > 1 else ""
            print(f"Problem{s} Found:")
            print()
            for i, problem in enumerate(problems):
                print(
                    f"{i + 1:{str(max_len)}d}) "
                    + str(problem).replace(  # index problem  # print problem
                        "\n", "\n" + " " * (max_len + 2)
                    )
                )  # fix indentation
                print()

    def add_final_options(self, space=True, back=True, exit=True):
        if space:
            self.add_space()
        if back:
            self.add_option("b", "Go Back", Menu.CLOSE)
        if exit:
            self.add_option("0", "Exit", sys.exit)

    def longest_label(self):
        lengths = [
            len(option) for option in self.get_options(include_hidden=False)
        ]
        return max(lengths)

    @classmethod
    def clear_screen(cls):
        os.system("cls" if os.name == "nt" else "clear")

    # clear the screen
    # show the options
    def show(self):
        if self.auto_clear:
            self.clear_screen()
        if self.problems_enabled:
            self.print_problems()
        if self.is_title_enabled:
            self.print_title()
        if self.is_message_enabled:
            print(self.message)
            print()
        label_width = self.longest_label()
        for label, option in self.options.items():
            if label not in self.gap_ids:
                if label in self.message_ids:
                    print(option[0].format(**option[1]))
                elif label not in self.hidden_options:
                    show_label = "[" + label + "] "
                    print(f"{show_label:<{label_width + 3}s}" + option[0])
            else:
                print()
        print()

    def func_wrapper(self, func):
        func()
        self.close()

    # show the menu
    # get the option index from the input
    # return the corresponding option handler
    def input(self):
        if len(self.options) == 0:
            return Menu.CLOSE
        self.show()

        with ListCompleter(self.get_options()):
            while True:
                try:
                    index = str(input(self.prompt + " ")).strip()
                    option = self.options[index]
                    handler = option[1]
                    if handler == Menu.CLOSE:
                        return Menu.CLOSE, False, False
                    kwargs = option[2]
                    return (
                        lambda: handler(**kwargs),
                        index in self.wait_options,
                        index in self.close_options,
                    )
                except (ValueError, IndexError):
                    return self.input(), False, False
                except KeyError:
                    print("Error: Invalid input")

    def CLOSE(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if any([self.space, self.back, self.exit]):
            self.add_final_options(self.space, self.back, self.exit)
        self.run()
