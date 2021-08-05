from ichor.arguments import Arguments
from ichor.globals.globals import Globals
from ichor.globals.machine import Machine
from ichor.globals.os import OS

__all__ = ["GLOBALS", "Machine", "OS"]

with Arguments():
    GLOBALS = Globals.define()
