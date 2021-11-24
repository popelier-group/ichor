from abc import ABC, abstractmethod
from typing import IO

import numpy as np


class Mean(ABC):
    """Abstract base class for implementing different mean functions for a Gaussian Process."""

    @abstractmethod
    def value(self, x: np.ndarray) -> np.ndarray:
        pass

    @abstractmethod
    def write(self, f: IO):
        pass
