from functools import wraps
from typing import Any, Sequence

from ichor.typing import F


def run_function(order: int) -> F:
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            func.order = order
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_functions_to_run(obj: Any) -> Sequence[F]:
    return sorted(
        [
            getattr(obj, field)
            for field in dir(obj)
            if hasattr(getattr(obj, field), "order")
        ],
        key=(lambda field: field.order),
    )
