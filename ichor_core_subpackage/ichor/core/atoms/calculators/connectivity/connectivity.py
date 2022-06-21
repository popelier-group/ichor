import numpy as np
from typing_extensions import Protocol


class ConnectivityCalculatorFunction(Protocol):
    def __call__(self, atoms: "Atoms", *args, **kwargs) -> np.ndarray:
        ...
