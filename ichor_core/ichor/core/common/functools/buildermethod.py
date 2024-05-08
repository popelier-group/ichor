from functools import wraps

from ichor.core.common.types.itypes import F, T


def buildermethod(func: F) -> F:
    """
    Executes a function on an instance of a class and returns the modified instance.
    This allows for scenarios where we can initialize a class and call a method
    (which does not return anything but it does modify the instance) in the same line.

    :param func: The function to be executed

    .. note::

        Without builder decorator:
            t = Test().add() Since the add() method does not return anything, t is `None`

        With @builder decorator:
            t = Test().add() Since the add() method does not return anything, t is an instance of test

        Without builder method:
        t = Test()
        t.add()
    """

    # makes sure that func.__name__ returns the name of the
    # function instead of wrapper if the decorator has been applied to func
    @wraps(func)
    def wrapper(self: T, *args, **kwargs) -> T:
        func(self, *args, **kwargs)
        return self

    return wrapper
