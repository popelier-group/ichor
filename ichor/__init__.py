# TODO: The docstring from this file will be the first thing a user sees in the documentation. So better to make a bullet point list
# TODO: of the main things that ICHOR can do
"""ICHOR links together the programs Gaussian, AIMALL and FEREBUS. Gaussian produces .wfn files which are then fed into AIMALL to partition a given system
into topological atoms. The topological atoms have unique energies/multipole moments which are used as the labels for Gaussian Process Regression (GPR) machine 
learning. ICHOR can automatically run Gaussian-AIMALL-FEREBUS jobs on CSF3 (see auto-run), but it can also be used more generally of CSF3 for submitting 
Gaussian/AIMALL jobs. """

import inspect
import os
from pathlib import Path

from ichor import in_main

filetrace = [i.filename for i in inspect.stack(0)]
in_main._IN_MAIN = os.path.relpath(filetrace[-1], Path(__file__).parent) == (Path('..') / 'ichor3.py')

from ichor.globals import GLOBALS

__all__ = ["GLOBALS"]
