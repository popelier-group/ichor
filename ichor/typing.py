""" Common type annotations used throughout ICHOR"""

from typing import Any, Callable, TypeVar, Union

import numpy as np

F = TypeVar("F", bound=Callable[..., Any])  # Function
T = TypeVar("T", bound=Any)  # anything

Scalar = TypeVar(
    "Scalar", bound=Union[int, float, np.int, np.float]
)  # a single number
