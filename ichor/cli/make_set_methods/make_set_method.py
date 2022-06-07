from abc import ABC, abstractmethod
from typing import List

from ichor.core.atoms import ListOfAtoms


class MakeSetMethod(ABC):
    """Abstract base class for making different methods by which to add points to the training set."""

    @classmethod
    @abstractmethod
    def name(cls) -> str:
        pass

    @classmethod
    @abstractmethod
    def get_npoints(cls, npoints: int, points: ListOfAtoms) -> int:
        pass

    @abstractmethod
    def get_points(self, points: ListOfAtoms) -> List[int]:
        pass
