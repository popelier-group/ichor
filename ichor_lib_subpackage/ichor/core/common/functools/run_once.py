from functools import wraps

from ichor.core.itypes import F


def run_once(func: F) -> F:
    """Decorator which only runs the function the first time it is called and stores the result. If the function is ran another time, the stored result is
    returned."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        if hasattr(func, "has_run"):
            return func.return_value
        func.return_value = func(*args, **kwargs)
        func.has_run = True
        return func.return_value

    return wrapper
