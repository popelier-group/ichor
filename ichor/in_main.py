from functools import wraps
from typing import Any

from ichor.typing import F

_IN_MAIN = False


def main_only(f: F) -> F:
    @wraps(f)
    def wrapper(*args, **kwargs) -> Any:
        if _IN_MAIN:
            return f(*args, **kwargs)

    return wrapper
