from abc import ABC


class Points(ABC, list):
    def __getattr__(self, item):
        if item in self.__dict__:
            return self.__dict__[item]
        else:
            return [getattr(point, item) for point in self]
