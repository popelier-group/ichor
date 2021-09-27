from abc import ABC


class VarReprMixin(ABC):
    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(f'{var}:{repr(value)}' for var, value in vars(self).items())})"
