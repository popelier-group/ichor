from abc import ABC


class NoStr(ABC):
    def __str__(self):
        raise ValueError(f"Cannot represent '{self.__class__.__name__}' as string")
