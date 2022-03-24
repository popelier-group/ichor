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

from ichor.common.types import Version
__version__ = Version("3.0.1")

def ichor_main():

    from ichor.batch_system import BATCH_SYSTEM
    from ichor.globals import GLOBALS
    from ichor.machine import MACHINE
    from ichor.arguments import Arguments
    from ichor import in_main
    from ichor.main import main_menu
    import sys
    __all__ = ["GLOBALS", "MACHINE", "BATCH_SYSTEM", "__version__"]

    in_main.IN_MAIN = True

    Arguments.read()
    GLOBALS.init_from_config(Arguments.config_file)
    GLOBALS.UID = Arguments.uid
    if Arguments.call_external_function:
        Arguments.call_external_function(
            *Arguments.call_external_function_args
        )
        sys.exit(0)

    main_menu()
