from functools import wraps

from ichor.typing import F, T


def buildermethod(func: F) -> F:
    @wraps(func)
    def wrapper(self: T, *args, **kwargs) -> T:
        func(self, *args, **kwargs)
        return self

    return wrapper
