from abc import ABC, abstractmethod


class FeatureCalculator(ABC):
    @abstractmethod
    def calculate_features(self, atoms):
        pass
