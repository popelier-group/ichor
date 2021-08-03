from functools import wraps

from ichor.typing import F, T


def buildermethod(func: F) -> F:
    """Executes a function on an instance of a class and returns the modified instance
    :param func: The function to be executed
    """
    @wraps(func)  # makes sure that func.__name__ returns the name of the function instead of wrapper if the decorator has been applied to func
    def wrapper(self: T, *args, **kwargs) -> T:
        func(self, *args, **kwargs)
        return self

    return wrapper
