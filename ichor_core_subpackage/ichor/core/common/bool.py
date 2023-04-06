from typing import Union


def check_bool(val: Union[str, bool], default: bool = True):
    """Convert a string value to a boolean value and return the boolean

    :param val: A string or boolean value.
        If a boolean value is given, return this directly. If a string value is given, check
        if it should return True of False.
    :param default: Whether or not to accept no input, i.e. "" as True.
    """
    if isinstance(val, str):
        options = ["true", "1", "t", "y", "yes", "yeah"]
        if default:
            options += [""]
        return val.lower() in options
    elif isinstance(val, bool):
        return val
    else:
        raise TypeError(f"Cannot convert type {type(val)} to bool")
