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
    def group(self) -> bool:
        return True

    @classproperty
    def ncores(self) -> int:
        return 1

    @classproperty
    def rerun(self) -> bool:
        """Whether to rerun points if they fail, up to GLOBALS.GAUSSIAN_N_TRIES"""
        from ichor.hpc import GLOBALS

        return GLOBALS.RERUN_POINTS

    @classproperty
    def scrub(self) -> bool:
        """Whether to remove failed points from a PointsDirectory and move them to a separate location, so they are not
        used in training/validating."""
        from ichor.hpc import GLOBALS

        return GLOBALS.SCRUB_POINTS

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
