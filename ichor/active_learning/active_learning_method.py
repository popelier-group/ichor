from abc import ABC, abstractmethod
from typing import List
from ichor.atoms import ListOfAtoms
from ichor.common.functools import classproperty
from ichor.models import Models


class ActiveLearningMethod(ABC):
    def __init__(self, models: Models):
        self.models = models

    @abstractmethod
    @classproperty
    def name(self) -> str:
        """Name of the expected improvement function to be selected from GLOBALS."""
        pass

    @abstractmethod
    def get_points(self, points: ListOfAtoms, npoints: int) -> List[int]:
        pass

    def __call__(self, points: ListOfAtoms, npoints: int) -> List[int]:
        return self.get_points(points, npoints)
