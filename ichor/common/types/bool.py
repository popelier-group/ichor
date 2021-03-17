from typing import Union


def check_bool(val: Union[str, bool], default: bool = True):
    if isinstance(val, str):
        options = ["true", "1", "t", "y", "yes", "yeah"]
        if default:
            options += [""]
        return val.lower() in options
    elif isinstance(val, bool):
        return val
    else:
        raise TypeError(f"Cannot convert type {type(val)} to bool")
