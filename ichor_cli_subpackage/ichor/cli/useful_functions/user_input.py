from ichor.cli.completers.tab_completer import PathCompleter
from typing import Union

def user_input_path(s="Enter Path: ") -> str:
    """Returns user input path.
    
    :param s: A string that is shown in the prompt (printed to standard output).
    """

    with PathCompleter(): 
        path = input(s)
    
    return path

def user_input_int(s="Enter integer: ") -> Union[int,None]:
    """Returns an integer that user has given

    :param s: A string that is shown in the prompt (printed to standard output).
    """

    while True:
        user_input = input(s)
        if user_input == "":
            return
        try:
            user_input = int(user_input)
            return user_input
        except:
            pass

def user_input_bool(s="Enter True/False: ") -> Union[bool, None]:
    """Returns True or False depending on user input
    
    :param s: A string that is shown in the prompt (printed to standard output).
    """

    while True:
        user_input = input(s)
        if user_input.lower() in ["t", "true", "1"]:
            return True
        elif user_input.lower() in ["f", "false", "0"]:
            return False
        elif user_input == "":
            return