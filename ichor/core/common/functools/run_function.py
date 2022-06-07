from functools import wraps
from typing import Any, Sequence

from ichor.core.itypes import F, Scalar


def run_function(order: Scalar) -> F:
    """Used to decorate a method so that `get_functions_to_run` can find and return the methods in
    the order specified by the order parameter"""

    def decorator(func: F) -> F:
        func._order = order

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_functions_to_run(obj: Any) -> Sequence[F]:
    """Finds all methods of `obj` with the `order` attribute then returns the sequence of methods
    in the order defined"""
    return sorted(
        [
            getattr(obj, field)
            for field in dir(obj)
            if hasattr(getattr(obj, field), "_order")
        ],
        key=(lambda field: field._order),
    )
