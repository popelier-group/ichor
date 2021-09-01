from abc import ABC, abstractmethod
from typing import List

from ichor.atoms import ListOfAtoms
from ichor.models import Models
from ichor.common.functools import classproperty


class ExpectedImprovement(ABC):
    def __init__(self, models: Models):
        self.models = models

    @abstractmethod
    @classproperty
    def name(self) -> str:
        """ Name of the expected improvement function to be selected from GLOBALS. """
        pass

    @abstractmethod
    def __call__(self, points: ListOfAtoms, npoints: int) -> List[int]:
        pass
