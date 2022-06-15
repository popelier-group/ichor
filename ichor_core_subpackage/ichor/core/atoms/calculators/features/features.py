from typing import Protocol

import numpy as np


class FeatureCalculatorFunction(Protocol):
    def __call__(self, atom: "Atom", *args, **kwargs) -> np.ndarray:
        ...
