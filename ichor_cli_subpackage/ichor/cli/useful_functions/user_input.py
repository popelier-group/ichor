from ichor.cli.completers.tab_completer import TabCompleter, PathCompleter

def user_input_path(s="Enter Path: ") -> str:
    """Returns user input path.
    
    :param s: A string that is shown in the prompt (printed to standard output).
    """

    with PathCompleter(): 
        path = input(s)
    
    return path