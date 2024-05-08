from typing import TypeVar

from ichor.core.files.path_object import PathObject

PathType = TypeVar("PathType", bound=PathObject)


class OptionalContentType:
    def exists(self):
        return False

    def __bool__(self):
        return False

    def __nonzero__(self):
        return False


OptionalContent = OptionalContentType()
