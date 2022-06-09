from abc import ABC, abstractmethod

class FeatureCalculatorNotFound(Exception):
    pass

class FeatureCalculator(ABC):
    @abstractmethod
    def calculate_features(self, atoms: "Atoms"):
        pass
