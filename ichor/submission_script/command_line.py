from abc import ABC, abstractmethod
from typing import List

from ichor.common.functools import classproperty
from ichor.modules import Modules


class SubmissionError(Exception):
    pass


class CommandLine(ABC):
    """Abstract Base Class for job types (such as Gaussian, AIMALL, and FEREBUS jobs.)"""

    @classproperty
    @abstractmethod
    def command(self) -> str:
        pass

    @classproperty
    def group(self) -> bool:
        return True

    @classproperty
    def ncores(self) -> int:
        return 1

    @property
    def ndata(self) -> int:
        return len(self.data)

    @property
    def data(self) -> List[str]:
        return []

    @classproperty
    def modules(self) -> Modules:
        return Modules()

    @classproperty
    def arguments(self) -> List[str]:
        return []

    @classproperty
    def options(self) -> List[str]:
        return []

    @abstractmethod
    def repr(self, variables: List[str]) -> str:
        pass
