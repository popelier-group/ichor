import numpy as np
from typing_extensions import Protocol


class FeatureCalculatorFunction(Protocol):
    def __call__(self, atom: "Atom", *args, **kwargs) -> np.ndarray:
        ...
