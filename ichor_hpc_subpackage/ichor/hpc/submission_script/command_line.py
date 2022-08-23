from abc import ABC, abstractmethod
from typing import List

from ichor.core.common.functools import classproperty
from ichor.hpc.modules import Modules


class SubmissionError(Exception):
    pass


class CommandLine(ABC):
    """Abstract Base Class for job types (such as Gaussian, AIMALL, and FEREBUS jobs.)"""

    @classproperty
    @abstractmethod
    def command(self) -> str:
        pass

    @classproperty
    @abstractmethod
    def modules(self) -> Modules:
        pass

    @classproperty
    @abstractmethod
    def group(self) -> bool:
        pass

    @property
    @abstractmethod
    def data(self) -> List[str]:
        pass
    
    @property
    def ndata(self) -> int:
        return len(self.data)

    @abstractmethod
    def repr(self, variables: List[str], *args, **kwargs) -> str:
        pass

    @property
    def arguments(self) -> List[str]:
        return []

    @property
    def options(self) -> List[str]:
        return []