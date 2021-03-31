from typing import Sequence


class RangeDict(dict):
    def __getitem__(self, item: int) -> str:
        for key, (minval, maxval) in self.items():
            if minval <= item <= maxval:
                return key
        raise KeyError(f"'{item}' not found in '{self.__class__.__name__}'")

    def __setitem__(self, key: str, value: [int, int]):
        if not isinstance(key, str):
            raise TypeError(f"Key for '{self.__class__.__name__}' must be of type 'str'")
        if not len(value) == 2:
            raise TypeError(f"Value for '{self.__class__.__name__}' must be a sequence of length 2")
        super().__setitem__(key, (value[0], value[1]))
