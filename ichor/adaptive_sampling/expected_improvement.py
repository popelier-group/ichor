from abc import ABC, abstractmethod
from ichor.atoms import ListOfAtoms
from ichor.models import Models
from typing import List


class ExpectedImprovement(ABC):
    def __init__(self, models: Models):
        self.models = models

    @abstractmethod
    def __call__(self, points: ListOfAtoms) -> List[int]:
        pass
