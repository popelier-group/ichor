from abc import ABC, abstractmethod
from typing import List

from ichor.core.atoms import ListOfAtoms


class MakeSetMethod(ABC):
    """Abstract base class for making different methods by which to add points to the training set."""

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        pass

    @staticmethod
    @abstractmethod
    def get_points_indices(self, points: ListOfAtoms) -> List[int]:
        pass
