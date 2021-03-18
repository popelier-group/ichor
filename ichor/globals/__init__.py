from ..arguments import Arguments
from .globals import Globals

__all__ = ["GLOBALS"]

Arguments.read()
GLOBALS = Globals.define()
