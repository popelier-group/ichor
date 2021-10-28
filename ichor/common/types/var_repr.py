from abc import ABC


class VarReprMixin(ABC):
    """ Abstract Base Class that is just used to add a __repr__ method to other classes instead of coding it in each class separately."""

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(f'{var}:{repr(value)}' for var, value in vars(self).items())})"
