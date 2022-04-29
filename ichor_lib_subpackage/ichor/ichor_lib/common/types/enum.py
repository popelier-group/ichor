from enum import Enum
from typing import Any

from ichor.ichor_lib.common.functools import classproperty
from ichor.ichor_lib.common.str import in_sensitive


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


class EnumStrList(Enum):
    """Extension of Enum where each enumeration is a list of strings to be searched through when initialising an enumeration"""

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for item in cls:
                if in_sensitive(value, item.value):
                    return item
        return super()._missing_(value)
