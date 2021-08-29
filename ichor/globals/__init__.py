""" GLOBALS is an instance which holds all important settings information for all programs (ICHOR, Gaussian, AIMALL, Ferebus). It has default options as
defined in globals.py, but these can be overwritten using an ICHOR config file. GLOBALS also determine imporatnt values/keywords depending on the machine (CSF3/FFLUXLAB)
that ICHOR is being ran on."""

from ichor.arguments import Arguments
from ichor.globals.globals import Globals
from ichor.globals.machine import Machine

__all__ = ["GLOBALS", "Machine"]

with Arguments():
    GLOBALS = Globals.define()
