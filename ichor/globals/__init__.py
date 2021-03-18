from ..arguments import Arguments
from .globals import Globals

__all__ = ["GLOBALS"]

with Arguments():
    GLOBALS = Globals.define()
