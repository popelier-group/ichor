import numpy as np

from ichor.models.mean.mean import Mean


class ConstantMean(Mean):
    def __init__(self, value: float):
        self._value = value

    def value(self, x: np.ndarray) -> float:
        return self._value

    def values(self, x: np.ndarray) -> np.ndarray:
        return np.full((x.shape[0]), self._value)
