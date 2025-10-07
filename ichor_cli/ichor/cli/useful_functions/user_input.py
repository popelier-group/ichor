from typing import List, Union

from ichor.cli.completers import PathCompleter


def bool_to_str(b: bool) -> str:
    """Converts True/False bool to yes/no str

    :param b: True or False
    :return: yes or no str
    """

    if b:
        return "yes"
    return "no"


def user_input_path(s="Enter Path: ", default_path=".") -> str:
    """Returns user input path.

    :param s: A string that is shown in the prompt (printed to standard output).
    """

    with PathCompleter():
        try:
            path = input(s)
        except EOFError:
            return default_path

    return path


def user_input_int(s="Enter integer: ", default=None) -> Union[int, None]:
    """Returns an integer that user has given

    :param s: A string that is shown in the prompt (printed to standard output).
    """

    while True:
        # if pressing ctrl + D, will return to previous menu
        try:
            user_input = input(s)
        except EOFError:
            return default
        if user_input == "":
            return default
        try:
            user_input = int(user_input)
            return user_input
        except ValueError:
            pass


def user_input_float(s="Enter float: ", default=None) -> Union[int, None]:
    """Returns a float that user has given

    :param s: A string that is shown in the prompt (printed to standard output).
    """

    while True:
        # if pressing ctrl + D, will return to previous menu
        try:
            user_input = input(s)
        except EOFError:
            return default
        if user_input == "":
            return default
        try:
            user_input = float(user_input)
            return user_input
        except ValueError:
            pass


def user_input_bool(s="Enter True/False: ", default=None) -> Union[bool, None]:
    """Returns True or False depending on user input

    :param s: A string that is shown in the prompt (printed to standard output).
    """

    while True:
        # if pressing ctrl + D, will return to previous menu
        try:
            user_input = input(s)
        except EOFError:
            return default
        if user_input.lower() in ["t", "true", "1", "yes", "y"]:
            return True
        elif user_input.lower() in ["f", "false", "0", "no", "n"]:
            return False
        elif user_input == "":
            return default


def user_input_free_flow(s="Enter str: ", default=None) -> str:
    """Asks user for inputs and returns whatever user has typed

    :param s: A string that is shown in the prompt (printed to standard output).
    """

    # if pressing ctrl + D, will return to previous menu
    try:
        user_input = input(s)
    except EOFError:
        return default
    if user_input == "":
        return default
    return user_input


def user_input_restricted(
    available_options: List[str], s="Enter str: ", default=None
) -> str:
    """Asks user for inputs and returns whatever user has typed

    :param s: A string that is shown in the prompt (printed to standard output).

    .. note::
        Additional info is displayed because the string is modified to show
        the available options in the function
    """

    available_options = [a.lower() for a in available_options]
    s = "Available options: " + ", ".join(map(str, available_options)) + "\n" + s

    # if pressing ctrl + D, will return to previous menu
    while True:
        try:
            user_input = input(s).lower()
        except EOFError:
            return default
        if user_input == "":
            return default
        elif user_input in available_options:
            return user_input.lower()
