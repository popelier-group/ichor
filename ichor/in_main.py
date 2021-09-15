from ichor.typing import F
from functools import wraps

from typing import Any

IN_MAIN = False


def main_only(f: F) -> F:
    @wraps(f)
    def wrapper(*args, **kwargs) -> Any:
        if IN_MAIN:
            return f(*args, **kwargs)
    return wrapper
