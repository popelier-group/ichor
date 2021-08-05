from typing import Any, Callable, TypeVar, Union

import numpy as np

F = TypeVar("F", bound=Callable[..., Any])  # Function
T = TypeVar("T", bound=Any)

Scalar = TypeVar("Scalar", bound=Union[int, float, np.int, np.float])
