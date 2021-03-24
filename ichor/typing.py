from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])  # Function
T = TypeVar('T', bound=Any)
