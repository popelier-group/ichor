from functools import wraps

from ichor.typing import F


def run_once(func: F) -> F:
    @wraps(func)
    def wrapper(*args, **kwargs):
        if hasattr(func, "has_run"):
            return func.return_value
        func.return_value = func(*args, **kwargs)
        func.has_run = True
        return func.return_value

    return wrapper
