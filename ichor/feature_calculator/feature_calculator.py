from abc import ABC, abstractmethod

import numpy as np


class FeatureCalculator(ABC):
    @abstractmethod
    def calculate_feature(self, geometry) -> np.ndarray:
        pass
