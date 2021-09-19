"""
    ###############################################
    #.####..######..##.....##..#######..########..#
    #..##..##....##.##.....##.##.....##.##.....##.#
    #..##..##.......##.....##.##.....##.##.....##.#
    #..##..##.......#########.##.....##.########..#
    #..##..##.......##.....##.##.....##.##...##...#
    #..##..##....##.##.....##.##.....##.##....##..#
    #.####..######..##.....##..#######..##.....##.#
    ###############################################

    Authors: Matthew Burn (matthew.burn@postgrad.manchester.ac.uk)
             Yulian Manchev (yulian.manchev@postgrad.manchester.ac.uk)
    Version: 3.0.0

    ICHOR is a gaussian process regression machine learning pipeline application
    for generating atomistic models for use in molecular dynamics simulations in
    the force field DL_FFLUX. ICHOR interfaces quantum chemical programs such as
    Gaussian, quantum chemical topology programs such as AIMAll and gaussian
    process regression software such as FEREBUS to make the generation of machine
    learning models as simple as possible.

    ICHOR has also been designed as a general purpose library for interfacing with
    many complex systems such as interfacing with input and output files from quantum
    chemistry programs, interfacing with the batch system to create and submit
    submission scripts as well as many other extremely common tasks for the computational
    chemist.

    Use and abuse all that ICHOR has to offer, there will be bugs but don't be afraid to
    jump into the code to try and fix it. Thanks to the hard work of Yulian, most of the
    code should be well documented but feel free to ask as many questions as you like
    we will be more than happy to help.
"""

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
# ^^^^ todo: may not be needed after arguments refactor, may be worth a check

from ichor.globals import GLOBALS

__all__ = ["GLOBALS"]
