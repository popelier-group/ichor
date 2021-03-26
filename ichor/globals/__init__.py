from ichor.arguments import Arguments
from ichor.globals.globals import Globals
from ichor.globals.machine import Machine

__all__ = ["GLOBALS", "Machine"]

with Arguments():
    GLOBALS = Globals.define()
