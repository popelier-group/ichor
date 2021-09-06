from abc import ABC, abstractmethod

import numpy as np


class Mean(ABC):
    """Abstract base class for implementing different mean functions for a Gaussian Process."""

    @abstractmethod
    def value(self, x: np.ndarray) -> float:
        pass

    @abstractmethod
    def values(self, x: np.ndarray) -> np.ndarray:
        pass
