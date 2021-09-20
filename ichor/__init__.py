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


from ichor.globals import GLOBALS

__all__ = ["GLOBALS"]
