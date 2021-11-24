from abc import ABC, abstractmethod
from typing import List, Optional

import numpy as np

from ichor.atoms import ListOfAtoms
from ichor.common.functools import classproperty
from ichor.common.numpy import batched_array
from ichor.globals import GLOBALS
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
    def get_points(self, points: ListOfAtoms, npoints: int) -> np.ndarray:
        """
        Method which gets the indices of the points to be added from the sample pool to the training set based on active learning criteria.
        """
        pass

    def batch_points(
        self, points: ListOfAtoms, batch_size: Optional[int] = None
    ):
        batch_size = batch_size or GLOBALS.BATCH_SIZE
        return batched_array(points, batch_size)

    def __call__(self, points: ListOfAtoms, npoints: int) -> np.ndarray:
        """Once an instance of an `ActiveLearningMethod` has been created, the instance can be called as a function (which will then
        go into this __call__ method and execute self.get_points() which is defined in each subclass of `ActiveLearningMethod`"""
        return self.get_points(points, npoints)
