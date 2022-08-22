from abc import ABC, abstractmethod
from typing import List

from ichor.core.common.functools import classproperty
from ichor.hpc.modules import Modules


class SubmissionError(Exception):
    pass


class CommandLine(ABC):
    """Abstract Base Class for job types (such as Gaussian, AIMALL, and FEREBUS jobs.)"""

    def __init__(self, ncores=1, scrub: bool = False, rerun: bool = False,):
        
        self.ncores = ncores
        self.scrub = scrub
        self.rerun = rerun

    @classproperty
    @abstractmethod
    def command(self) -> str:
        pass

    @classproperty
    @abstractmethod
    def modules(self) -> Modules:
        pass

    @property
    @abstractmethod
    def group(self) -> bool:
        return True

    @property
    @abstractmethod
    def data(self) -> List[str]:
        pass

    @property
    def arguments(self) -> List[str]:
        return []

    @property
    def options(self) -> List[str]:
        return []

    @property
    def repr(self, variables: List[str]) -> str:
        pass
    
    @property
    def ndata(self) -> int:
        return len(self.data)