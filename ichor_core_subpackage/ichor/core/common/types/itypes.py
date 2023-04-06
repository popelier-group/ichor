""" Common type annotations used throughout ICHOR"""

from typing import Any, Callable, TypeVar, Union

F = TypeVar("F", bound=Callable[..., Any])  # Function
T = TypeVar("T", bound=Any)  # anything

Scalar = TypeVar("Scalar", bound=Union[int, float])  # a single number
