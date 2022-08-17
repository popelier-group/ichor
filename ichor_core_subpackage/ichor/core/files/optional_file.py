from typing import TypeVar, Union

from ichor.core.files import PathObject

PathType = TypeVar("PathType", bound=PathObject)


class OptionalFileType:
    def exists(self):
        return False

    def __bool__(self):
        return False

    def __nonzero__(self):
        return False


OptionalFile = OptionalFileType()

OptionalPath = Union[PathType, OptionalFileType]
