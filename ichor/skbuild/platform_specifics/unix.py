"""This module defines object specific to Unix platform."""

from . import abstract
from .abstract import CMakeGenerator


# pylint:disable=abstract-method
class UnixPlatform(abstract.CMakePlatform):
    """Unix implementation of :class:`.abstract.CMakePlatform`."""

    def __init__(self):
        super(UnixPlatform, self).__init__()
        self.default_generators = [
            CMakeGenerator("Ninja"),
            CMakeGenerator("Unix Makefiles"),
        ]
