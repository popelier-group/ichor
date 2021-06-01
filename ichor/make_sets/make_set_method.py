from abc import ABC, abstractmethod
from typing import List

from ichor.atoms import ListOfAtoms


class MakeSetMethod(ABC):
    @classmethod
    @abstractmethod
    def name(cls) -> str:
        pass

    @abstractmethod
    def get_points(self, points: ListOfAtoms) -> List[int]:
        pass
