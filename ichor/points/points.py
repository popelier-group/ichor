from abc import ABC

from ichor.atoms import ListOfAtoms


class Points(ABC, ListOfAtoms):
    def __getattr__(self, item):
        try:
            return [getattr(point, item) for point in self]
        except AttributeError:
            raise AttributeError(
                f"'{self.__class__.__name__}' has no attribute '{item}'"
            )
