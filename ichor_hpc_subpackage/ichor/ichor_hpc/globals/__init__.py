""" GLOBALS is an instance which holds all important settings information for all programs (ICHOR, Gaussian, AIMALL, Ferebus). It has default options as
defined in globals.py, but these can be overwritten using an ICHOR config file. GLOBALS also determine imporatnt values/keywords depending on the machine (CSF3/FFLUXLAB)
that ICHOR is being ran on."""

from pathlib import Path

from ichor.common.os import input_with_prefill
from ichor.globals.globals import Globals
from ichor.globals.os import OS

GLOBALS = Globals()