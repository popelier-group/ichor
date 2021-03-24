from abc import ABC
from ichor.common.functools import buildermethod


class Points(ABC, list):
    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        else:
            return [getattr(point, item) for point in self]
