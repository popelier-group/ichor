from enum import Enum
from typing import Any

from ichor.common.functools import classproperty


class Enum(Enum):
    """Extension of the builtin Enum class"""

    @classproperty
    def names(cls):
        return [e.name for e in cls]

    @classproperty
    def values(cls):
        return [e.value for e in cls]

    @classmethod
    def as_dict(cls):
        return {e.name: e.value for e in cls}

    @classmethod
    def from_name(cls, name: str):
        return cls.__members__[name]

    @classmethod
    def from_value(cls, value: Any):
        return cls(value)
