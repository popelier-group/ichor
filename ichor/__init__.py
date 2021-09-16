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

filetrace = [i.filename for i in inspect.stack(0)] # returns a list of the full paths to the files which are executed, we do not want extra context lines so set to 0

# doing this prevent Arguments from being ran when using ichor as a library only.
# todo: the way this is set up now means that the file needs to be called ichor3.py in order for it to be ran as CLI instead of library
# the commented out way works, but errors are if the files are not on the same disks as no relative path can be made on separate disks.
# in_main._IN_MAIN = os.path.relpath(filetrace[-1], Path(__file__).parent) == (Path('..') / 'ichor3.py')
in_main._IN_MAIN = Path(filetrace[-1]).name == Path("ichor3.py")


from ichor.globals import GLOBALS

__all__ = ["GLOBALS"]
