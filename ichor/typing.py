from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])
