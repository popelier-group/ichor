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

# initialize all things that we need for the hpc package here

import platform
import sys
from pathlib import Path

from ichor.core.common.types import Version
from ichor.hpc.arguments import Arguments
from ichor.hpc.batch_system import (
    SLURM,
    LocalBatchSystem,
    ParallelEnvironments,
    SunGridEngine,
)
from ichor.hpc.file_structure import FileStructure
from ichor.hpc.globals import Globals
from ichor.hpc.log import setup_logger
from ichor.hpc.machine import (
    Machine,
    get_machine_from_name,
    get_machine_from_file,
)
from ichor.core.common.io import mkdir, move
from ichor.hpc.uid import get_uid

__version__ = Version("3.1.0")

FILE_STRUCTURE = FileStructure()

BATCH_SYSTEM = LocalBatchSystem
if SunGridEngine.is_present():
    BATCH_SYSTEM = SunGridEngine
if SLURM.is_present():
    BATCH_SYSTEM = SLURM

machine_name: str = platform.node()
# will be Machine.Local if machine is not in list of names
MACHINE = get_machine_from_name(machine_name)

PARALLEL_ENVIRONMENT = ParallelEnvironments()
PARALLEL_ENVIRONMENT[Machine.csf3]["smp.pe"] = 2, 32
PARALLEL_ENVIRONMENT[Machine.csf4]["serial"] = 1, 1
PARALLEL_ENVIRONMENT[Machine.csf4]["multicore"] = 2, 32
PARALLEL_ENVIRONMENT[Machine.ffluxlab]["smp"] = 2, 44

GLOBALS = Globals()

logger = setup_logger("ICHOR", "ichor.log")
timing_logger = setup_logger("TIMING", "ichor.timing")


def init_machine():
    # if machine has been successfully identified, write to FILE_STRUCTURE['machine']
    if MACHINE is not Machine.local and (
        not FILE_STRUCTURE["machine"].exists()
        or FILE_STRUCTURE["machine"].exists()
        and get_machine_from_file() != MACHINE
    ):
        mkdir(FILE_STRUCTURE["machine"].parent)
        machine_filepart = Path(
            str(FILE_STRUCTURE["machine"]) + f".{get_uid()}.filepart"
        )
        with open(machine_filepart, "w") as f:
            f.write(f"{MACHINE.name}")
        move(machine_filepart, FILE_STRUCTURE["machine"])


def ichor_main():
    global GLOBALS
    global MACHINE

    Arguments.read()
    GLOBALS.init_from_config(Arguments.config_file)
    GLOBALS.UID = Arguments.uid
    init_machine()
    if Arguments.call_external_function:
        Arguments.call_external_function(
            *Arguments.call_external_function_args
        )
        sys.exit(0)


# probably don't need that file because the platform name should match
# if machine has been successfully identified, write to FILE_STRUCTURE['machine']
# if MACHINE is not Machine.local and (
#     not FILE_STRUCTURE["machine"].exists()
#     or (
#         FILE_STRUCTURE["machine"].exists()
#         and not get_machine_from_file() is None
#     )
# ):
#     mkdir(FILE_STRUCTURE["machine"].parent)
#     machine_filepart = Path(
#         str(FILE_STRUCTURE["machine"]) + f".{get_uid()}.filepart"
#     )
#     with open(machine_filepart, "w") as f:
#         f.write(f"{MACHINE.name}")
#     move(machine_filepart, FILE_STRUCTURE["machine"])
