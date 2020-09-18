#! python3
"""
  #############################################################################################################
  #:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::#
  #::#######################################################################################################::#
  #::#                                                                                                     #::#
  #::#  IIIIIIIIII         CCCCCCCCCCCCC HHHHHHHHH     HHHHHHHHH      OOOOOOOOO      RRRRRRRRRRRRRRRRR     #::#
  #::#  I::::::::I      CCC::::::::::::C H:::::::H     H:::::::H    OO:::::::::OO    R::::::::::::::::R    #::#
  #::#  I::::::::I    CC:::::::::::::::C H:::::::H     H:::::::H  OO:::::::::::::OO  R::::::RRRRRR:::::R   #::#
  #::#  II::::::II   C:::::CCCCCCCC::::C HH::::::H     H::::::HH O:::::::OOO:::::::O RR:::::R     R:::::R  #::#
  #::#    I::::I    C:::::C       CCCCCC   H:::::H     H:::::H   O::::::O   O::::::O   R::::R     R:::::R  #::#
  #::#    I::::I   C:::::C                 H:::::H     H:::::H   O:::::O     O:::::O   R::::R     R:::::R  #::#
  #::#    I::::I   C:::::C                 H::::::HHHHH::::::H   O:::::O     O:::::O   R::::RRRRRR:::::R   #::#
  #::#    I::::I   C:::::C                 H:::::::::::::::::H   O:::::O     O:::::O   R:::::::::::::RR    #::#
  #::#    I::::I   C:::::C                 H:::::::::::::::::H   O:::::O     O:::::O   R::::RRRRRR:::::R   #::#
  #::#    I::::I   C:::::C                 H::::::HHHHH::::::H   O:::::O     O:::::O   R::::R     R:::::R  #::#
  #::#    I::::I   C:::::C                 H:::::H     H:::::H   O:::::O     O:::::O   R::::R     R:::::R  #::#
  #::#    I::::I    C:::::C       CCCCCC   H:::::H     H:::::H   O::::::O   O::::::O   R::::R     R:::::R  #::#
  #::#  II::::::II   C:::::CCCCCCCC::::C HH::::::H     H::::::HH O:::::::OOO:::::::O RR:::::R     R:::::R  #::#
  #::#  I::::::::I    CC:::::::::::::::C H:::::::H     H:::::::H  OO:::::::::::::OO  R::::::R     R:::::R  #::#
  #::#  I::::::::I      CCC::::::::::::C H:::::::H     H:::::::H    OO:::::::::OO    R::::::R     R:::::R  #::#
  #::#  IIIIIIIIII         CCCCCCCCCCCCC HHHHHHHHH     HHHHHHHHH      OOOOOOOOO      RRRRRRRR     RRRRRRR  #::#
  #::#                                                                                                     #::#
  #::#######################################################################################################::#
  #:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::#
  #############################################################################################################
  Author:  Matthew Burn
  Version: 2.1
  Date: 19-11-2019

  ICHOR Design Principles:
  -- All within one script, this is up for debate however this script currently requires high portabilty and therefore
     is being designed within one script
  -- GLOBALS are in all caps and defined at the top of the script below the import statements
  -- Classes are defined next
  -- Functions are defined after Classes
  -- Main script is written beneath which calls functions when needed
  -- Main Menu is at the bottom, this should be easy to extend and is hopefully quite intuitive

  TODO
  [x]| Description                                                                                | Priority
  -----------------------------------------------------------------------------------------------------------
  [ ] Implement incomplete menu options (indicated with ||)                                       |
  [ ] Add CP2K support                                                                            |
  [ ] Merge makeSets into ICHOR                                                                   |    x
  [ ] Make SGE Queue names more meaningful ('GaussSub.sh' -> 'WATER G09 1')                       |
  [x] Cleanup SubmissionScript Implementation                                                     |
  [ ] Implement More Kernels Into ICHOR                                                           |
  [ ] Make a Revert System / Backup System                                                        |
  [x] Move EPE calculation to an independent function so more EI Algorithms can be implemented    |
  [x] Cleanup Training Set formation implementation so that any X and y values can be used        |
  [ ] Implement method of locking functions based on what is currently running (e.g. Auto Run)    |
  [x] Create a Globals class to cleanup how ICHOR handles global variables                        |
  [ ] Make 'rewind' option (move added training points back to sample pool)                       |
  [ ] Make stop auto run flag when an error occurs                                                |
  [ ] Convert to pathlib                                                                          |
  [ ] Add get timing from ichor log and AIMAll log to tools                                       |—
"""

#############################################
#                  Imports                  #
#############################################

# Standard Library
import os
import re
import io
import sys
import ast
import math
import time
import uuid
import json
import atexit
import shutil
import random
import hashlib
import logging
import inspect
import platform
import warnings
import importlib
import contextlib
import subprocess
from glob import glob
import itertools as it
from pathlib import Path
from signal import SIGTERM
from getpass import getpass
from functools import wraps
import multiprocessing as mp
from functools import lru_cache
from argparse import ArgumentParser

# Required imports
import numpy as np
from tqdm import tqdm
from numba import jit
from scipy import stats
from numpy import linalg as la
from scipy.spatial import distance

#############################################
#                  Globals                  #
#############################################

GLOBALS = None

# Below are only for SSH settings which isn't implemented yet
EXTERNAL_MACHINES = {
    "csf3": "csf3.itservices.manchester.ac.uk",
    "ffluxlab": "ffluxlab.mib.manchester.ac.uk",
}

SSH_SETTINGS = {
    "machine": "",
    "working_directory": "",
    "username": "",
    "password": "",
}

#############################################
#:::::::::::::::::::::::::::::::::::::::::::#
#############################################


def setup_logger(name, log_file, level=logging.INFO, formatter=logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%d-%m-%Y %H:%M:%S")):
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    new_logger = logging.getLogger(name)
    new_logger.setLevel(level)
    new_logger.addHandler(handler)

    return new_logger


logger = setup_logger("ICHOR", "ichor.log")
timing_logger = setup_logger("TIMING", "ichor.timing")

_data_lock = False

try:
    O_BINARY = os.O_BINARY
except:
    O_BINARY = 0
READ_FLAGS = os.O_RDONLY | O_BINARY
WRITE_FLAGS = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | O_BINARY
BUFFER_SIZE = 128 * 1024

#############################################
#             Class Definitions             #
#############################################


class Constants:
    BOAQ_VALUES = [
        "auto",
        "gs1",
        "gs2",
        "gs3",
        "gs4",
        "gs5",
        "gs6",
        "gs7",
        "gs8",
        "gs9",
        "gs10",
        "gs15",
        "gs20",
        "gs25",
        "gs30",
        "gs35",
        "gs40",
        "gs45",
        "gs50",
        "gs55",
        "gs60",
        "leb23",
        "leb25",
        "leb27",
        "leb29",
        "leb31",
        "leb32",
    ]

    IASMESH_VALUES = ["sparse", "medium", "fine", "veryfine", "superfine"]

    GAUSSIAN_METHODS = [
        "AM1",
        "PM3",
        "PM3MM",
        "PM6",
        "PDDG",
        "PM7",
        "HF",
        "CASSCF",
        "MP2",
        "MP3",
        "MP4(SDQ)",
        "MP4(SDQ,full)",
        "MP4(SDTQ)",
        "MP5",
        "BD",
        "CCD",
        "CCSD",
        "QCISD",
        "BD(T)",
        "CCSD(T)",
        "QCISD(T)",
        "BD(TQ)",
        "CCSD(TQ)",
        "QCISD(TQ)",
        "EPT",
        "CBS",
        "GN",
        "W1",
        "CIS",
        "TD",
        "EOM",
        "ZINDO",
        "DFTB",
        "CID",
        "CISD",
        "GVB",
        "S",
        "XA",
        "B",
        "PW91",
        "mPW",
        "G96",
        "PBE",
        "O",
        "TPSS",
        "BRx",
        "PKZB",
        "wPBEh",
        "PBEh",
        "VWN",
        "VWN5",
        "LYP",
        "PL",
        "P86",
        "PW91",
        "B95",
        "PBE",
        "TPSS",
        "KCIS",
        "BRC",
        "PKZB",
        "VP86",
        "V5LYP",
        "HFS",
        "XAlpha",
        "HFB",
        "VSXC",
        "HCTH",
        "HCTH93",
        "HCTH147",
        "HCTH407",
        "tHCTH",
        "M06L",
        "B97D",
        "B97D3",
        "SOGGA11",
        "M11L",
        "N12",
        "MN12L",
        "B3LYP",
        "B3P86",
        "B3PW91",
        "B1B95",
        "mPW1PW91",
        "mPW1LYP",
        "mPW1PBE",
        "mPW3PBE",
        "B98",
        "B971",
        "B972",
        "PBE1PBE",
        "B1LYP",
        "O3LYP",
        "BHandH",
        "BHandHLYP",
        "BMK",
        "M06",
        "M06HF",
        "M062X",
        "tHCTHhyb",
        "APFD",
        "APF",
        "SOGGA11X",
        "PBEh1PBE",
        "TPSSh",
        "X3LYP",
        "HSEH1PBE",
        "OHSE2PBE",
        "OHSE1PBE",
        "wB97XD",
        "wB97",
        "wB97X",
        "LC-wPBE",
        "CAM-B3LYP",
        "HISSbPBE",
        "M11",
        "N12SX",
        "MN12SX",
        "LC-",
    ]

    AIMALL_FUNCTIONALS = ["MO62X", "B3LYP", "PBE"]

    FEREBUS_VERSIONS = ["fortran", "python"]

    type2mass = {
        "H": 1.007825,
        "He": 4.002603,
        "Li": 7.016005,
        "Be": 9.012182,
        "B": 11.009305,
        "C": 12.0,
        "N": 14.003074,
        "O": 15.994915,
        "F": 18.998403,
        "Ne": 19.99244,
        "Na": 22.989769,
        "Mg": 23.985042,
        "Al": 26.981539,
        "Si": 27.976927,
        "P": 30.973762,
        "S": 31.972071,
        "Cl": 34.968853,
        "Ar": 39.962383,
        "K": 38.963707,
        "Ca": 39.962591,
        "Sc": 44.955912,
        "Ti": 47.947946,
        "V": 50.94396,
        "Cr": 51.940508,
        "Mn": 54.938045,
        "Fe": 55.9349382,
        "Co": 58.933195,
        "Ni": 57.935343,
        "Cu": 62.929598,
        "Zn": 63.929142,
        "Ga": 68.925574,
        "Ge": 73.921178,
        "As": 74.921597,
        "Se": 79.916521,
        "Br": 78.918337,
        "Kr": 83.911507,
    }

    type2rad = {
        "H": 0.37,
        "He": 0.32,
        "Li": 1.34,
        "Be": 0.9,
        "B": 0.82,
        "C": 0.77,
        "N": 0.74,
        "O": 0.73,
        "F": 0.71,
        "Ne": 0.69,
        "Na": 1.54,
        "Mg": 1.3,
        "Al": 1.18,
        "Si": 1.11,
        "P": 1.06,
        "S": 1.02,
        "Cl": 0.99,
        "Ar": 0.97,
        "K": 1.96,
        "Ca": 1.74,
        "Sc": 1.44,
        "Ti": 1.36,
        "V": 1.25,
        "Cr": 1.27,
        "Mn": 1.39,
        "Fe": 1.25,
        "Co": 1.26,
        "Ni": 1.21,
        "Cu": 1.38,
        "Zn": 1.31,
        "Ga": 1.26,
        "Ge": 1.22,
        "As": 1.19,
        "Se": 1.16,
        "Br": 1.14,
        "Kr": 1.1,
    }

    dlpoly_weights = {
        "H": 1.007975,
        "He": 4.002602,
        "Li": 6.9675,
        "Be": 9.0121831,
        "B": 10.8135,
        "C": 12.0106,
        "N": 14.006855,
        "O": 15.9994,
        "F": 18.99840316,
        "Ne": 20.1797,
        "Na": 22.98976928,
        "Mg": 24.3055,
        "Al": 26.9815385,
        "Si": 28.085,
        "P": 30.973762,
        "S": 32.0675,
        "Cl": 35.4515,
        "Ar": 39.948,
        "K": 39.0983,
        "Ca": 40.078,
        "Sc": 44.955908,
        "Ti": 47.867,
        "V": 50.9415,
        "Cr": 51.9961,
        "Mn": 54.938044,
        "Fe": 55.845,
        "Co": 58.933194,
        "Ni": 58.6934,
        "Cu": 63.546,
        "Zn": 65.38,
        "Ga": 69.723,
        "Ge": 72.63,
        "As": 74.921595,
        "Se": 78.971,
        "Br": 79.904,
        "Kr": 83.798,
        "Rb": 85.4678,
        "Sr": 87.62,
        "Y": 88.90584,
        "Zr": 91.224,
        "Nb": 92.90637,
        "Mo": 95.95,
    }

    multipole_names = [
        "q00",
        "q10",
        "q11c",
        "q11s",
        "q20",
        "q21c",
        "q21s",
        "q22c",
        "q22s",
        "q30",
        "q31c",
        "q31s",
        "q32c",
        "q32s",
        "q33c",
        "q33s",
        "q40",
        "q41c",
        "q41s",
        "q42c",
        "q42s",
        "q43c",
        "q43s",
        "q44c",
        "q44s",
    ]

    ha_to_kj_mol = 2625.5


class UsefulTools:
    @staticmethod
    # @property
    def ichor_logo():
        ichor_encoded_string = [
            '"%s %s%s %s%s%s %s%s%s %s%s" % ("I"*10," "*8,"C"*13,"H"*9," "*5,"H"*9," "*5,"O"*9,'
            '" "*5,"R"*17," "*3)',
            '"%s%s%s %s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s %s%s%s%s" % ("I",":"*8,"I"," "*5,"C"*3,":"*12,"C","H",":"*7,"H"'
            '," "*5,"H",":"*7,"H"," "*3,"O"*2,":"*9,"O"*2," "*3,"R",":"*16,"R"," "*2)',
            '"%s%s%s %s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s %s%s%s%s%s%s" % ("I",":"*8,"I"," "*3,"C"*2,":"*15,"C","H",":"*7'
            ',"H"," "*5,"H",":"*7,"H"," ","O"*2,":"*13,"O"*2," ","R",":"*6,"R"*6,":"*5,"R"," ")',
            '"%s%s%s %s%s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s %s%s%s%s%s%s%s" % ("I"*2,":"*6,"I"*2," "*2,"C",":"*5,"C"*8,'
            '":"*4,"C","H"*2,":"*6,"H"," "*5,"H",":"*6,"H"*2,"O",":"*7,"O"*3,":"*7,"O","R"*2,":"*5,"R"," "*5,"R",'
            '":"*5,"R")',
            '"%s%s%s%s%s %s%s%s%s%s%s %s%s%s%s%s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s%s%s%s" % (" "*2,"I",":"*4,"I"," "*2,'
            '" ","C",":"*5,"C"," "*7,"C"*6," "*2,"H",":"*5,"H"," "*5,"H",":"*5,"H"," "*2,"O",":"*6,"O"," "*3,"O",":"*6,"O"'
            '," "*2,"R",":"*4,"R"," "*5,"R",":"*5,"R")',
            '"%s%s%s%s%s %s%s%s%s %s%s%s%s%s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s%s%s%s" % (" "*2,"I",":"*4,"I"," "*2,"C",'
            '":"*5,"C"," "*14," "*2,"H",":"*5,"H"," "*5,"H",":"*5,"H"," "*2,"O",":"*5,"O"," "*5,"O",":"*5,"O"," "*2,"R",'
            '":"*4,"R"," "*5,"R",":"*5,"R")',
            '"%s%s%s%s%s %s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s%s%s" % (" "*2,"I",":"*4,"I"," "*2,"C",":"*5,'
            '"C"," "*14," "*2,"H",":"*6,"H"*5,":"*6,"H"," "*2,"O",":"*5,"O"," "*5,"O",":"*5,"O"," "*2,"R",":"*4,"R"*6,'
            '":"*5,"R"," ")',
            '"%s%s%s%s%s %s%s%s%s %s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s" % (" "*2,"I",":"*4,"I"," "*2,"C",":"*5,"C",'
            '" "*14," "*2,"H",":"*17,"H"," "*2,"O",":"*5,"O"," "*5,"O",":"*5,"O"," "*2,"R",":"*13,"R"*2," "*2)',
            '"%s%s%s%s%s %s%s%s%s %s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s%s%s" % (" "*2,"I",":"*4,"I"," "*2,"C",":"*5,'
            '"C"," "*14," "*2,"H",":"*17,"H"," "*2,"O",":"*5,"O"," "*5,"O",":"*5,"O"," "*2,"R",":"*4,"R"*6,":"*5,"R"," ")',
            '"%s%s%s%s%s %s%s%s%s %s%s%s%s%s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s%s%s%s" % (" "*2,"I",":"*4,"I"," "*2,"C",'
            '":"*5,"C"," "*14," "*2,"H",":"*5,"H"," "*5,"H",":"*5,"H"," "*2,"O",":"*5,"O"," "*5,"O",":"*5,"O"," "*2,"R",'
            '":"*4,"R"," "*5,"R",":"*5,"R")',
            '"%s%s%s%s%s %s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s%s%s%s" % (" "*2,"I",":"*4,"I"," "*2,"C",'
            '":"*5,"C"," "*14," "*2,"H",":"*6,"H"*5,":"*6,"H"," "*2,"O",":"*5,"O"," "*5,"O",":"*5,"O"," "*2,"R",":"*4,"R",'
            '" "*5,"R",":"*5,"R")',
            '"%s%s%s%s%s %s%s%s%s%s%s %s%s%s%s%s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s%s%s%s" % (" "*2,"I",":"*4,"I"," "*2,'
            '" ","C",":"*5,"C"," "*7,"C"*6," "*2,"H",":"*5,"H"," "*5,"H",":"*5,"H"," "*2,"O",":"*6,"O"," "*3,"O",":"*6,"O"'
            '," "*2,"R",":"*4,"R"," "*5,"R",":"*5,"R")',
            '"%s%s%s %s%s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s %s%s%s%s%s%s%s" % ("I"*2,":"*6,"I"*2," "*2,"C",":"*5,"C"*8,'
            '":"*4,"C","H"*2,":"*6,"H"," "*5,"H",":"*6,"H"*2,"O",":"*7,"O"*3,":"*7,"O","R"*2,":"*5,"R"," "*5,"R",":"*5,'
            '"R")',
            '"%s%s%s %s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s %s%s%s%s%s%s%s" % ("I",":"*8,"I"," "*3,"C"*2,":"*15,"C","H",'
            '":"*7,"H"," "*5,"H",":"*7,"H"," ","O"*2,":"*13,"O"*2," ","R",":"*6,"R"," "*5,"R",":"*5,"R")',
            '"%s%s%s %s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s %s%s%s%s%s%s%s" % ("I",":"*8,"I"," "*5,"C"*3,":"*12,"C","H",'
            '":"*7,"H"," "*5,"H",":"*7,"H"," "*3,"O"*2,":"*9,"O"*2," "*3,"R",":"*6,"R"," "*5,"R",":"*5,"R")',
            '"%s %s%s %s%s%s %s%s%s %s%s%s" % ("I"*10," "*8,"C"*13,"H"*9," "*5,"H"*9," "*5,"O"*9," "*5,"R"*8," "*5,'
            '"R"*7)',
        ]

        ichor_string = ("{}\n" * 23).format(
            "#" * 109,
            "#%s#" % (":" * 107),
            "#::%s::#" % ("#" * 103),
            "#::#%s#::#" % (" " * 101),
            "#::#  %s  #::#" % eval(ichor_encoded_string[0]),
            "#::#  %s  #::#" % eval(ichor_encoded_string[1]),
            "#::#  %s  #::#" % eval(ichor_encoded_string[2]),
            "#::#  %s  #::#" % eval(ichor_encoded_string[3]),
            "#::#  %s  #::#" % eval(ichor_encoded_string[4]),
            "#::#  %s  #::#" % eval(ichor_encoded_string[5]),
            "#::#  %s  #::#" % eval(ichor_encoded_string[6]),
            "#::#  %s  #::#" % eval(ichor_encoded_string[7]),
            "#::#  %s  #::#" % eval(ichor_encoded_string[8]),
            "#::#  %s  #::#" % eval(ichor_encoded_string[9]),
            "#::#  %s  #::#" % eval(ichor_encoded_string[10]),
            "#::#  %s  #::#" % eval(ichor_encoded_string[11]),
            "#::#  %s  #::#" % eval(ichor_encoded_string[12]),
            "#::#  %s  #::#" % eval(ichor_encoded_string[13]),
            "#::#  %s  #::#" % eval(ichor_encoded_string[14]),
            "#::#  %s  #::#" % eval(ichor_encoded_string[15]),
            "#::#%s#::#" % (" " * 101),
            "#::%s::#" % ("#" * 103),
            "#%s#" % (":" * 107),
            "#" * 109,
        )
        return ichor_string

    @staticmethod
    def nTrain():
        ts_dir = GLOBALS.FILE_STRUCTURE["training_set"]
        return FileTools.count_points_in(ts_dir)

    @staticmethod
    def natural_sort(iterable, reverse=False):
        prog = re.compile(r"(\d+)")

        def alphanum_key(element):
            return [int(c) if c.isdigit() else c for c in prog.findall(element)]

        return sorted(iterable, key=alphanum_key, reverse=reverse)

    @staticmethod
    def natural_sort_path(iterable, reverse=False):
        prog = re.compile(r"(\d+)")

        def alphanum_key(element):
            return [int(c) if c.isdigit() else c for c in prog.findall(element.path)]

        return sorted(iterable, key=alphanum_key, reverse=reverse)

    @staticmethod
    def natural_sort_atom(iterable, reverse=False):
        prog = re.compile(r"(\d+)")

        def alphanum_key(element):
            return [int(c) if c.isdigit() else c for c in prog.findall(element.atom)]

        return sorted(iterable, key=alphanum_key, reverse=reverse)

    @staticmethod
    def count_digits(n):
        import math

        return math.floor(math.log(n, 10) + 1)

    @staticmethod
    def check_bool(val, default=True):
        if isinstance(val, str):
            options = ["true", "1", "t", "y", "yes", "yeah"]
            if default:
                options += [""]
            return val.lower() in options
        elif isinstance(val, bool):
            return val

    @staticmethod
    def print_grid(arr, cols=10, color=None):
        import math

        ncols, _ = shutil.get_terminal_size(fallback=(80, 24))
        width = math.floor(ncols * 0.9 / cols)
        rows = math.ceil(len(arr) / cols)
        for i in range(rows):
            row = ""
            for j in range(cols):
                indx = cols * i + j
                if indx >= len(arr):
                    break
                fname = arr[indx]
                string = f"{fname:{str(width)}s}"
                if fname == "scratch":
                    row += Colors.OKGREEN + string + Colors.ENDC
                else:
                    if color:
                        string = color + string + Colors.ENDC
                    row += string
                row = row + "\t" if len(fname) > width else row
            print(row)

    @staticmethod
    def in_sensitive(string, array, case=True, whitespace=True):
        def modify(s):
            s = s.upper() if case else s
            s = s.strip().replace(" ", "") if whitespace else s
            return s

        return modify(string) in map(modify, array)

    @staticmethod
    def unpack(s):
        return " ".join(map(str, s))

    @staticmethod
    def run_function(order):
        def do_assignment(to_func):
            to_func.order = order
            return to_func

        return do_assignment

    @staticmethod
    def get_functions_to_run(obj):
        return sorted(
            [
                getattr(obj, field)
                for field in dir(obj)
                if hasattr(getattr(obj, field), "order")
            ],
            key=(lambda field: field.order),
        )

    @staticmethod
    def external_function(*args):
        def run_func(func):
            name = args[0] if args else func.__name__
            Arguments.external_functions[name] = func
            return func

        return run_func

    @staticmethod
    def add_method(cls, name=None):
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                return func(*args, **kwargs)

            if not name:
                name = func.__name__
            setattr(cls, name, wrapper)
            # Note we are not binding func, but wrapper which accepts self but does exactly the same as func
            return func  # returning func means func can still be used normally

        return decorator

    @staticmethod
    def get_widths(line, ignore_chars=[]):
        pc = line[0]
        widths = [0]
        found_char = False
        for i, c in enumerate(line):
            if c != " ":
                found_char = True
            if pc == " " and c != " " and found_char and c not in ignore_chars:
                widths.append(i - 1)
            pc = c
        widths.append(len(line))
        return sorted(list(set(widths)))

    @staticmethod
    def split_widths(line, widths, strip=False):
        line_split = []
        for lower, upper in zip(widths[:-1], widths[1:]):
            str_slice = line[lower:upper]
            if strip:
                str_slice = str_slice.strip()
            line_split.append(str_slice)
        return line_split

    @staticmethod
    def format_list(l, n):
        if n > len(l):
            for _ in range(len(l), n):
                l += [0]
        return l[:n]

    @staticmethod
    def suppress_output():
        text_trap = io.StringIO()
        sys.stdout = text_trap

    @staticmethod
    def tqdm(iterator, *args, **kwargs):
        return iterator

    @staticmethod
    def suppress_tqdm():
        global tqdm
        tqdm = my_tqdm

    @staticmethod
    def not_implemented():
        raise NotImplementedError

    @staticmethod
    def prettify_string(string):
        string = string.replace("_", " ").split()
        for i, word in enumerate(string):
            if len(word) > 1:
                string[i] = word[0].upper() + word[1:].lower()
        return " ".join(string)

    @staticmethod
    def get_time():
        return time.time()

    @staticmethod
    def log_time_taken(start_time, message=""):
        time_taken = UsefulTools.get_time() - start_time
        logger.debug(f"{message}{time_taken:.2f} s")

    @staticmethod
    def get_uid():
        return str(uuid.uuid4())

    @staticmethod
    def set_uid(uid=None):
        if GLOBALS.SUBMITTED and GLOBALS.UID:
            return
        GLOBALS.UID = uid if uid else UsefulTools.get_uid()

    @staticmethod
    def input_with_prefill(prompt, prefill=""):
        try:
            # Readline only available on Unix
            import readline

            readline.set_startup_hook(lambda: readline.insert_text(str(prefill)))
            return input(prompt)
        except:
            return input(prompt)
        finally:
            try:
                import readline

                readline.set_startup_hook()
            except:
                pass

    @staticmethod
    def get_number(s):
        return int("".join(c for c in s if c.isdigit()))


class GlobalTools:
    @staticmethod
    def cleanup_str(s):
        s = s.replace('"', "")
        s = s.replace("'", "")
        s = s.strip()
        return s

    @staticmethod
    def to_upper(s):
        return s.upper()

    @staticmethod
    def to_lower(s):
        return s.lower()

    @staticmethod
    def split_keywords(keywords):
        split_keywords = []
        if isinstance(keywords, str):
            keywords = keywords.replace("[", "")
            keywords = keywords.replace("]", "")
            split_keywords = (
                keywords.split(",") if "," in keywords else keywords.split()
            )
        split_keywords = [
            GlobalTools.cleanup_str(keyword) for keyword in split_keywords
        ]
        return split_keywords

    @staticmethod
    def read_alf(alf):
        if isinstance(alf, str):
            alf = ast.literal_eval(alf)
        if isinstance(alf, list):
            alf = [[int(i) for i in j] for j in alf]
        return alf


class Arguments:
    config_file = "config.properties"
    uid = UsefulTools.get_uid()

    external_functions = {}
    call_external_function = None
    call_external_function_args = []

    @staticmethod
    def read():
        parser = ArgumentParser(description="ICHOR: A kriging training suite")

        parser.add_argument(
            "-c",
            "--config",
            dest="config_file",
            type=str,
            help="Name of Config File for ICHOR",
        )
        allowed_functions = ",".join(Arguments.external_functions.keys())
        parser.add_argument(
            "-f",
            "--func",
            dest="func",
            type=str,
            metavar=("func", "arg"),
            nargs="+",
            help=f"Call ICHOR function with args, allowed functions: [{allowed_functions}]",
        )
        parser.add_argument(
            "-u",
            "--uid",
            dest="uid",
            type=str,
            help="Unique Identifier For ICHOR Jobs To Write To",
        )

        args = parser.parse_args()
        if args.config_file:
            Arguments.config_file = args.config_file

        if args.func:
            func = args.func[0]
            func_args = args.func[1:] if len(args.func) > 1 else []
            if func in Arguments.external_functions.keys():
                Arguments.call_external_function = Arguments.external_functions[func]
                Arguments.call_external_function_args = func_args
            else:
                print(f"{func} not in allowed functions:")
                formatted_functions = [str(f) for f in allowed_functions.split(",")]
                formatted_functions = "- " + "\n- ".join(formatted_functions)
                print(f"{formatted_functions}")
                quit()

        if args.uid:
            Arguments.uid = args.uid


class GlobalVariable:
    type_conversions = {
        bool: UsefulTools.check_bool,
    }

    def __init__(self, name, value, type):
        self.name = name

        self.type = type
        self.modifiers = []
        self.pre_modifiers = []
        self.changed = False
        self.hidden = False
        self.allowed_values = []

        self.default = None
        self.changed = False
        self.in_config = False

        self.value = value

    def add_modifier(self, modifier):
        self.modifiers += [modifier]
        self.set(self.value)

    def add_pre_modifier(self, modifier):
        self.pre_modifiers += [modifier]
        self.set(self.value)

    def set(self, value):
        if "value" not in self.__dict__.keys():
            self.default = value
        else:
            self.changed = True

        for modifier in self.pre_modifiers:
            value = modifier(value)

        convert = (
            GlobalVariable.type_conversions[self.type]
            if self.type in GlobalVariable.type_conversions.keys()
            else self.type
        )
        # Make sure type is the correct type
        try:
            self.__dict__["value"] = (
                value if convert in Globals.types else convert(value)
            )
        except:
            self.__dict__["value"] = value

        for modifier in self.modifiers:
            self.__dict__["value"] = modifier(self.value)

        if self.type not in Globals.types:
            self.type = type(self.value)

    def __setattr__(self, key, val):
        if key == "value":
            self.set(val)
        else:
            self.__dict__[key] = val

    def __getattr__(self, key, *args):
        if key in self.__dict__.keys():
            return self.__dict__[key]
        else:
            try:
                return getattr(self.value, key)
            except:
                raise AttributeError(key)

    def details(self):
        return f"Value:   {self.value}\nType:    {self.type.__name__}\nHidden:  {self.hidden}\nDefault: {self.default}\nChanged: {self.changed}"

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __list__(self):
        return list(self.value)

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return repr(self.value)

    def __add__(self, other):
        return self.value + other

    def __radd__(self, other):
        return other + self.value

    def __sub__(self, other):
        return self.value - other

    def __rsub__(self, other):
        return other - self.value

    def __mul__(self, other):
        return self.value * other

    def __rmul__(self, other):
        return self.value * other

    def __truediv__(self, other):
        return self.value / other

    def __rtruediv__(self, other):
        return other / self.value

    def __neg__(self):
        return self.value.__neg__()

    def __pos__(self):
        return self.value.__pos__()

    def __abs__(self):
        return self.value.__abs__()

    def __invert__(self):
        return self.value.__invert__()

    def __getitem__(self, i):
        return self.value[i]

    def __delitem__(self, i):
        del self.value[i]

    def __bool__(self):
        return bool(self.value)

    def __len__(self):
        return len(self.value)

    def __next__(self):
        return next(self.value)

    def __iter__(self):
        return iter(self.value)

    def __index__(self):
        return self.value.__index__()

    def __hash__(self):
        return self.value.__hash__()

    def __lt__(self, other):
        return self.value.__lt__(other)

    def __le__(self, other):
        return self.value.__le__(other)

    def __gt__(self, other):
        return self.value.__gt__(other)

    def __ge__(self, other):
        return self.value.__ge__(other)

    def __unicode__(self):
        return self.value.__unicode__()

    def __format__(self, formatstr):
        return self.value.__format__(formatstr)

    def __sizeof__(self):
        return self.value.__sizeof__()

    # def items(self):
    #     return dict.items(self.value)


class Globals:
    types = []

    def __init__(self):
        pass

    @staticmethod
    def define():
        global GLOBALS

        name = __name__ if not __name__ == "*" else "__main__"
        for _, obj in inspect.getmembers(sys.modules[name]):
            if inspect.isclass(obj):
                Globals.types += [obj]

        globals = Globals()

        globals.SYSTEM_NAME = "SYSTEM", str

        globals.ALF_REFERENCE_FILE = (
            "",
            str,
        )  # set automatically if not defined
        globals.ALF = [], list

        globals.MAX_ITERATION = 1, int
        globals.POINTS_PER_ITERATION = 1, int

        globals.OPTIMISE_PROPERTY = "iqa", str

        globals.ADAPTIVE_SAMPLING_METHOD = "epe", str
        globals.NORMALISE = False, bool
        globals.STANDARDISE = False, bool

        globals.METHOD = "B3LYP", str
        globals.BASIS_SET = "6-31+g(d,p)", str
        globals.KEYWORDS = [], list

        globals.ENCOMP = 3, int
        globals.BOAQ = "gs20", str
        globals.IASMESH = "fine", str

        globals.FILE_STRUCTURE = Tree()  # Don't change

        globals.KERNEL = "rbf", str  # only use rbf for now
        globals.FEREBUS_VERSION = (
            "python",
            str,
        )  # fortran (FEREBUS) or python (FEREBUS.py)
        globals.FEREBUS_LOCATION = "PROGRAMS/FEREBUS", str

        # CORE COUNT SETTINGS FOR RUNNING PROGRAMS (SUFFIX CORE_COUNT)
        globals.GAUSSIAN_CORE_COUNT = 2, int
        globals.AIMALL_CORE_COUNT = 2, int
        globals.FEREBUS_CORE_COUNT = 4, int
        globals.DLPOLY_CORE_COUNT = 1, int

        # FEREBUS RUNTIME SETTINGS (PREFIX FEREBUS)
        globals.FEREBUS_SWARM_SIZE = (
            -1,
            int,
        )  # If negative >> Size dynamically allocated by FEREBUS
        globals.FEREBUS_NUGGET = (
            1.0e-10,
            float,
        )  # Default value for FEREBUS nugget
        globals.FEREBUS_MIN_THETA = (
            0.0,
            float,
        )  # Minimum theta value for initialisation (best to keep 0)
        globals.FEREBUS_MAX_THETA = (
            1.0,
            float,
        )  # Maximum theta value for initialisation

        globals.MAX_NUGGET = 1e-4, float

        globals.FEREBUS_COGNITIVE_LEARNING_RATE = 1.49400, float
        globals.FEREBUS_INERTIA_WEIGHT = 0.72900, float
        globals.FEREBUS_SOCIAL_LEARNING_RATE = 1.49400, float

        globals.FEREBUS_TOLERANCE = 1.0e-8, float
        globals.FEREBUS_CONVERGENCE = 20, int
        globals.FEREBUS_MAX_ITERATION = 10000, int

        # DLPOLY RUNTIME SETTINGS (PREFIX DLPOLY)
        globals.DLPOLY_NUMBER_OF_STEPS = (
            500,
            int,
        )  # Number of steps to run simulation for
        globals.DLPOLY_TEMPERATURE = (
            0,
            int,
        )  # If set to 0, will perform geom opt but default to 10 K
        globals.DLPOLY_PRINT_EVERY = (
            1,
            int,
        )  # Print trajectory and stats every n steps
        globals.DLPOLY_TIMESTEP = 0.001, float  # in ps
        globals.DLPOLY_LOCATION = "PROGRAMS/DLPOLY.Z", str

        globals.DLPOLY_CHECK_CONVERGENCE = False, bool
        globals.DLPOLY_CONVERGENCE_CRITERIA = -1, int

        globals.DLPOLY_MAX_ENERGY = -1.0, float
        globals.DLPOLY_MAX_FORCE = -1.0, float
        globals.DLPOLY_RMS_FORCE = -1.0, float
        globals.DLPOLY_MAX_DISP = -1.0, float
        globals.DLPOLY_RMS_DISP = -1.0, float

        # CP2K SETTINGS
        globals.CP2K_INPUT = "", str
        globals.CP2K_TEMPERATURE = 300, int  # K
        globals.CP2K_STEPS = 10000, int
        globals.CP2K_TIMESTEP = 1.0, float  # fs
        globals.CP2K_METHOD = "BLYP", str
        globals.CP2K_BASIS_SET = "6-31G*", str
        globals.CP2K_DATA_DIR = "", str

        # Recovery and Integration Errors
        globals.WARN_RECOVERY_ERROR = True, bool
        globals.RECOVERY_ERROR_THRESHOLD = (
            0.00038087983,
            float,
        )  # Ha (1.0 kJ/mol)

        globals.WARN_INTEGRATION_ERROR = True, bool
        globals.INTEGRATION_ERROR_THRESHOLD = 0.001, float  # Ha (1.0 kJ/mol)

        # Activate Warnings when making models
        globals.LOG_WARNINGS = False  # Gets set in _make_models

        globals.MACHINE = "", str
        globals.SGE = False, bool  # Don't Change
        globals.SUBMITTED = False, bool  # Don't Change

        globals.DISABLE_PROBLEMS = False, bool
        globals.UID = Arguments.uid

        globals.IQA_MODELS = False, bool

        globals.INCLUDE_NODES = [], list
        globals.EXCLUDE_NODES = [], list

        # Set Hidden Variables
        globals.FILE_STRUCTURE.hidden = True
        globals.SGE.hidden = True
        globals.SUBMITTED.hidden = True
        globals.UID.hidden = True
        globals.IQA_MODELS.hidden = True

        # Set Allowed Values
        globals.METHOD.allowed_values = Constants.GAUSSIAN_METHODS
        globals.BOAQ.allowed_values = Constants.BOAQ_VALUES
        globals.IASMESH.allowed_values = Constants.IASMESH_VALUES
        globals.FEREBUS_VERSION.allowed_values = Constants.FEREBUS_VERSIONS
        globals.OPTIMISE_PROPERTY.allowed_values = ["iqa"] + Constants.multipole_names

        # Set modifiers
        for global_variable in globals.global_variables:
            if globals.__dict__[global_variable].type == str:
                globals.__dict__[global_variable].add_modifier(GlobalTools.cleanup_str)
        globals.SYSTEM_NAME.add_modifier(GlobalTools.to_upper)
        globals.KEYWORDS.add_pre_modifier(GlobalTools.split_keywords)
        globals.ALF.add_pre_modifier(GlobalTools.read_alf)
        globals.OPTIMISE_PROPERTY.add_modifier(GlobalTools.to_lower)
        globals.INCLUDE_NODES.add_pre_modifier(GlobalTools.split_keywords)
        globals.EXCLUDE_NODES.add_pre_modifier(GlobalTools.split_keywords)

        globals.init()

        GLOBALS = globals
        return globals

    def init(self):
        global tqdm

        self.FILE_STRUCTURE = FileTools.setup_file_structure()

        # Set Machine Name
        machine_name = platform.node()
        if "csf3." in machine_name:
            self.MACHINE = "csf3"
        elif "csf2." in machine_name:
            self.MACHINE = "csf2"
        elif "ffluxlab" in machine_name:
            self.MACHINE = "ffluxlab"
        else:
            self.MACHINE = "local"

        # SGE settings
        self.SGE = "SGE_ROOT" in os.environ.keys()
        self.SUBMITTED = "SGE_O_HOST" in os.environ.keys()
        if self.SUBMITTED:
            tqdm = my_tqdm

        config = ConfigProvider(source=Arguments.config_file)

        for key, val in config.items():
            self.set(key, val)
            if key in self.__dict__.keys():
                self.__dict__[key].in_config = True
            else:
                ProblemFinder.unknown_settings += [key]

        if not self.ALF:
            if not self.ALF_REFERENCE_FILE:
                try:
                    self.ALF_REFERENCE_FILE = FileTools.get_first_gjf(
                        self.FILE_STRUCTURE["training_set"]
                    )
                except:
                    logger.warning("Cannot Find Training Set GJF")
                    try:
                        self.ALF_REFERENCE_FILE = FileTools.get_first_gjf(
                            self.FILE_STRUCTURE["sample_pool"]
                        )
                    except:
                        logger.warning("Cannot Find Sample Pool GJF")
                        try:
                            self.ALF_REFERENCE_FILE = FileTools.get_first_gjf(
                                self.FILE_STRUCTURE["validation_set"]
                            )
                        except:
                            logger.warning("Cannot Find Validation Set GJF")
                            logger.error("No ALF_REFERENCE_FILE Defined")
                            pass
            if self.ALF_REFERENCE_FILE:
                try:
                    GJF(str(self.ALF_REFERENCE_FILE)).read().atoms.calculate_alf()
                    self.ALF = Atoms.ALF
                except:
                    logger.error("Error When Calculating ALF")
                    print(
                        "\nError in ALF calculation, please specify file to calculate ALF"
                    )

    def set(self, name, value):
        name = name.upper()
        if name not in self.global_variables:
            ProblemFinder.unknown_settings.append(name)
        else:
            setattr(self, name, value)

    def items(self, show_hidden=False):
        items = []
        for global_variable in self.global_variables:
            var = self.__dict__[global_variable]
            if not var.hidden or show_hidden:
                items += [var]
        return items

    def save_to_properties_config(self, config_file, global_variables):
        with open(config_file, "w") as config:
            logo = UsefulTools.ichor_logo()
            config.write(f"{logo}\n\n")
            for key, val in global_variables.items():
                config.write(f"{key}={val}\n")

    def save_to_yaml_config(self, config_file, global_variables):
        import yaml

        with open(config_file, "w") as config:
            yaml.dump(global_variables, config)

    def save_to_config(self, config_file=Arguments.config_file):
        global_variables = {}
        for global_variable in self.items():
            if global_variable.changed or global_variable.in_config:
                global_variables[global_variable.name] = global_variable.value

        if config_file.endswith(".properties"):
            self.save_to_properties_config(config_file, global_variables)
        elif config_file.endswith(".yaml"):
            self.save_to_yaml_config(config_file, global_variables)

    @property
    def config_variables(self):
        config_variables = []
        for key, val in self.__dict__.items():
            if isinstance(val, GlobalVariable) and not val.hidden:
                config_variables += [key]
        return config_variables

    @property
    def global_variables(self):
        global_variables = []
        for key, val in self.__dict__.items():
            if isinstance(val, GlobalVariable):
                global_variables += [key]
        return global_variables

    def __setattr__(self, name, value):
        if name in self.global_variables:
            self.__dict__[name].value = value
        else:
            if type(value) in [list, tuple] and type(value[-1]) in [
                type,
                *Globals.types,
            ]:
                if len(value) > 2:
                    self.__dict__[name] = GlobalVariable(name, value[:-1], value[-1])
                else:
                    self.__dict__[name] = GlobalVariable(name, value[0], value[-1])
            else:
                self.__dict__[name] = GlobalVariable(name, value, type(value))

    def __getattr__(self, attr):
        if attr in self.global_variables:
            return self.__dict__[attr].value
        else:
            return self.__dict__[attr]


class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    @staticmethod
    def format_blue(s):
        return Colors.OKBLUE + s + Colors.ENDC


class Patterns:
    COORDINATE_LINE = re.compile(r"\s*\w+(\s*[+-]?\d+.\d+([Ee]?[+-]?\d+)?){3}")

    AIMALL_LINE = re.compile(r"[<|]?\w+[|>]?\s+=(\s+[+-]?\d+.\d+([Ee]?[+-]?\d+)?)")
    MULTIPOLE_LINE = re.compile(
        r"Q\[\d+,\d+(,\w+)?]\s+=\s+[+-]?\d+.\d+([Ee]?[+-]?\d+)?"
    )
    SCIENTIFIC = re.compile(r"[+-]?\d+.\d+([Ee]?[+-]?\d+)?")


class TabCompleter:
    def path_completer(self, text, state):
        try:
            import readline

            line = readline.get_line_buffer().split()
            if "~" in text:
                text = os.path.expanduser("~")
            if os.path.isdir(text):
                text += os.sep

            files = [x for x in glob(text + "*")]
            for i, f in enumerate(files):
                if os.path.isdir(f):
                    files[i] += os.sep
            return files[state]
        except ImportError:
            pass

    def create_list_completer(self, ll):
        def list_completer(text, state):
            try:
                import readline

                line = readline.get_line_buffer()
                if not line:
                    return [c + " " for c in ll][state]
                else:
                    return [c + " " for c in ll if c.startswith(line)][state]
            except ImportError:
                pass

        self.list_completer = list_completer

    def setup_completer(self, completer, pattern=None):
        try:
            import readline

            readline.set_completer_delims("\t")
            readline.parse_and_bind("tab: complete")
            readline.set_completer(completer)
        except ImportError:
            pass

    def remove_completer(self):
        try:
            import readline

            readline.set_completer(None)
        except ImportError:
            pass


class Menu(object):
    def __init__(
        self,
        options=None,
        title=None,
        message=None,
        prompt=">>",
        refresh=lambda *args: None,
        auto_clear=True,
        enable_problems=False,
        auto_close=False,
    ):
        if options is None:
            options = []
        self.options = None
        self.title = None
        self.is_title_enabled = None
        self.message = None
        self.is_message_enabled = None
        self.refresh = None
        self.prompt = None
        self.is_open = None
        self.auto_clear = auto_clear
        self.auto_close = auto_close
        self.problems_enabled = enable_problems

        self.gap_ids = []
        self.message_ids = []
        self.wait_options = []
        self.close_options = []
        self.hidden_options = []

        self.set_options(options)
        self.set_title(title)
        self.set_title_enabled(title is not None)
        self.set_message(message)
        self.set_message_enabled(message is not None)
        self.set_prompt(prompt)
        self.set_refresh(refresh)

    def set_options(self, options):
        original = self.options
        self.options = {}
        try:
            for option in options:
                if not isinstance(option, tuple):
                    raise TypeError(option, "option is not a tuple")
                if len(option) < 2:
                    raise ValueError(option, "option is missing a handler")
                kwargs = option[3] if len(option) == 3 else {}
                self.add_option(option[0], option[1], kwargs)
        except (TypeError, ValueError) as e:
            self.options = original
            raise e

    def set_title(self, title):
        self.title = title

    def set_title_enabled(self, is_enabled):
        self.is_title_enabled = is_enabled

    def set_message(self, message):
        self.message = message

    def set_message_enabled(self, is_enabled):
        self.is_message_enabled = is_enabled

    def set_prompt(self, prompt):
        self.prompt = prompt

    def set_refresh(self, refresh):
        if not callable(refresh):
            raise TypeError(refresh, "refresh is not callable")
        self.refresh = refresh

    def clear_options(self):
        self.options = None

        self.gap_ids = []
        self.message_ids = []
        self.wait_options = []
        self.close_options = []
        self.hidden_options = []

        self.set_options([])

    def get_options(self, include_hidden=True):
        return [
            label
            for label, option in self.options.items()
            if label not in self.gap_ids
            and label not in self.message_ids
            and (label not in self.hidden_options or include_hidden)
        ]

    def add_option(
        self,
        label,
        name,
        handler,
        kwargs={},
        wait=False,
        auto_close=False,
        hidden=False,
    ):
        if not callable(handler):
            raise TypeError(handler, "handler is not callable")
        self.options[label] = (name, handler, kwargs)
        if wait:
            self.wait_options.append(label)
        if auto_close:
            self.close_options.append(label)
        if hidden:
            self.hidden_options.append(label)

    def add_space(self):
        from uuid import uuid4

        gap_id = uuid4()
        self.gap_ids.append(gap_id)
        self.options[gap_id] = ("", "", {})

    def add_message(self, message, fmt={}):
        from uuid import uuid4

        message_id = uuid4()
        self.message_ids.append(message_id)
        self.options[message_id] = (message, fmt, {})

    # open the menu
    def run(self):
        self.is_open = True
        while self.is_open:
            self.refresh(self)
            func, wait, close = self.input()
            if func == Menu.CLOSE:
                func = self.close
            print()
            func()
            if close or self.auto_close:
                self.close()
            input("\nContinue...") if wait else None

    def close(self):
        self.is_open = False

    def print_title(self):
        print("#" * (len(self.title) + 4))
        print("# " + self.title + " #")
        print("#" * (len(self.title) + 4))
        print()

    def print_problems(self):
        problems = ProblemFinder()
        problems.find()
        if len(problems) > 0:
            max_len = UsefulTools.count_digits(len(problems))
            s = "s" if len(problems) > 1 else ""
            print(f"Problem{s} Found:")
            print()
            for i, problem in enumerate(problems):
                print(
                    f"{i+1:{str(max_len)}d}) "
                    + str(problem).replace(  # index problem  # print problem
                        "\n", "\n" + " " * (max_len + 2)
                    )
                )  # fix indentation
                print()

    def add_final_options(self, space=True, back=True, exit=True):
        if space:
            self.add_space()
        if back:
            self.add_option("b", "Go Back", Menu.CLOSE)
        if exit:
            self.add_option("0", "Exit", quit)

    def longest_label(self):
        lengths = []
        for option in self.get_options(include_hidden=False):
            lengths += [len(option)]
        return max(lengths)

    # clear the screen
    # show the options
    def show(self):
        if self.auto_clear:
            os.system("cls" if os.name == "nt" else "clear")
        if self.problems_enabled:
            self.print_problems()
        if self.is_title_enabled:
            self.print_title()
        if self.is_message_enabled:
            print(self.message)
            print()
        label_width = self.longest_label()
        for label, option in self.options.items():
            if label not in self.gap_ids:
                if label in self.message_ids:
                    print(option[0].format(**option[1]))
                elif label not in self.hidden_options:
                    show_label = "[" + label + "] "
                    print(f"{show_label:<{label_width+3}s}" + option[0])
            else:
                print()
        print()

    def func_wrapper(self, func):
        func()
        self.close()

    # show the menu
    # get the option index from the input
    # return the corresponding option handler
    def input(self):
        if len(self.options) == 0:
            return Menu.CLOSE
        self.show()

        t = TabCompleter()
        t.create_list_completer(self.get_options())
        t.setup_completer(t.list_completer)

        while True:
            try:
                index = str(input(self.prompt + " ")).strip()
                option = self.options[index]
                handler = option[1]
                if handler == Menu.CLOSE:
                    return Menu.CLOSE, False, False
                kwargs = option[2]
                return (
                    lambda: handler(**kwargs),
                    index in self.wait_options,
                    index in self.close_options,
                )
            except (ValueError, IndexError):
                return self.input(), False, False
            except KeyError:
                print("Error: Invalid input")

    def CLOSE(self):
        pass


class ConfigProvider(dict):
    """
    Class to read in a config file and create a dictionary of key, val pairs
    Parameters
    ----------
    source: String
          Optional parameter to specify the config file to read
          If no source file is specified, defaults to "config.properties"
    Example
    -------
    >>config.properties
    'SYSTEM_NAME=WATER
     DETERMINE_ALF=False
     ALF=[[1,2,3],[2,1,3],[3,1,2]]'
     {'SYSTEM_NAME': 'WATER', 'DETERMINE_ALF': 'False', 'ALF': '[[1,2,3],[2,1,3],[3,1,2]]'}
    Notes
    -----
    >> If you would like to interpret the config file as literals, 'import ast' and use ast.evaluate_literal()
       when reading in the key value
       -- Undecided on whether to automatically do this or leave it for the user to specify
       -- May add function to evaluate all as literals at some point which can then be 'switched' ON/OFF
    >> Included both .properties and .yaml file types, to add more just create a function to interpret it and add
       an extra condition to the if statement in loadConfig()
    """

    def __init__(self, source=Arguments.config_file):
        self.src = source
        self.load_config()

    def load_config(self):
        if self.src.endswith(".properties"):
            self.load_properties_config()
        elif self.src.endswith(".yaml"):
            self.load_yaml_config()

    def print_key_vals(self):
        for key in self:
            print("%s:\t%s" % (key, self[key]))

    def load_file_data(self):
        global _config_read_error
        try:
            with open(self.src, "r") as finput:
                return finput.readlines()
        except IOError:
            _config_read_error = True
        return ""

    def load_properties_config(self):
        for line in self.load_file_data():
            if not line.strip().startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                self[self.cleanup_key(key)] = val.strip()

    def load_yaml_config(self):
        import yaml

        entries = yaml.load(self.load_file_data())
        if entries:
            self.update(entries)

    def cleanup_key(self, key):
        return key.strip().replace(" ", "_").upper()

    def add_key_val(self, key, val):
        self[key] = val

    def write_key_vals(self):
        with open(self.src, "w+") as f:
            f.write(UsefulTools.ichor_logo())
            f.write("\n")
            for key in self:
                f.write("%s=%s\n" % (key, self[key]))


class Node:
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent

    def __str__(self):
        if self.parent is None:
            return self.name
        return str(self.parent) + os.sep + self.name

    def __repr__(self):
        return str(self)


class Tree:
    def __init__(self):
        self._dict = {}

    def add(self, name, id, parent=None):
        if parent is not None:
            parent = self[parent]
        self._dict[id] = Node(name, parent)

    def __getitem__(self, id):
        return str(self._dict[id])


class Daemon:
    """
    A generic daemon class.
    
    Usage: subclass the Daemon class and override the run() method

    Credit: Sander Marechal (https://bit.ly/3frF5RK)
    """

    def __init__(
        self, pidfile, stdin="/dev/null", stdout="/dev/null", stderr="/dev/null",
    ):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # exit first parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # decouple from parent environment
        cwd = os.getcwd()
        os.chdir("/")
        os.setsid()
        os.umask(0)
        os.chdir(cwd)

        # do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # exit from second parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        # si = open(self.stdin, "r")
        so = open(self.stdout, "a+")
        se = open(self.stderr, "a+")
        # os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        with open(self.pidfile, "w+") as pf:
            pf.write(f"{pid}\n")

    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile, "r") as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None

        if pid:
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            with open(self.pidfile, "r") as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return  # not an error in a restart

        # Try killing the daemon process
        try:
            while 1:
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print(str(err))
                sys.exit(1)

    def check(self):
        try:
            with open(self.pidfile, "r") as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None
        return not pid is None

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def run(self):
        pass


class FileTools:
    class CTError(Exception):
        def __init__(self, errors):
            self.errors = errors

    @staticmethod
    def copyfile(src, dst):
        try:
            fin = os.open(src, READ_FLAGS)
            stat = os.fstat(fin)
            fout = os.open(dst, WRITE_FLAGS, stat.st_mode)
            for x in iter(lambda: os.read(fin, BUFFER_SIZE), ""):
                os.write(fout, x)
        finally:
            try:
                os.close(fin)
            except:
                pass
            try:
                os.close(fout)
            except:
                pass

    @staticmethod
    def copytree(src, dst, symlinks=False, overwrite=True):
        names = os.listdir(src)
        if os.path.exists:
            if overwrite:
                FileTools.mkdir(dst, empty=overwrite)
            else:
                return
        errors = []
        for name in names:
            srcname = os.path.join(src, name)
            dstname = os.path.join(dst, name)
            try:
                if symlinks and os.path.islink(srcname):
                    linkto = os.readlink(srcname)
                    os.symlink(linkto, dstname)
                elif os.path.isdir(srcname):
                    FileTools.copytree(srcname, dstname, symlinks)
                else:
                    shutil.copy2(srcname, dstname)
                # XXX What about devices, sockets etc.?
            except OSError as why:
                errors.append((srcname, dstname, str(why)))
            # catch the Error from the recursive copytree so that we can
            # continue with other files
            except FileTools.CTError as err:
                errors.extend(err.args[0])
        try:
            shutil.copystat(src, dst)
        except OSError as why:
            # can't copy file access times on Windows
            if why.winerror is None:
                errors.extend((src, dst, str(why)))
        if errors:
            raise FileTools.CTError(errors)

    @staticmethod
    @contextlib.contextmanager
    def pushd(new_dir):
        previous_dir = os.getcwd()
        os.chdir(new_dir)
        try:
            yield
        finally:
            os.chdir(previous_dir)

    @staticmethod
    def clear_log(log_file="ichor.log"):
        with open(log_file, "w"):
            pass

    @staticmethod
    def setup_file_structure():
        tree = Tree()

        tree.add("TRAINING_SET", "training_set")
        tree.add("SAMPLE_POOL", "sample_pool")
        tree.add("VALIDATION_SET", "validation_set")
        tree.add("FEREBUS", "ferebus")
        tree.add("MODELS", "models", parent="ferebus")
        tree.add("LOG", "log")
        tree.add("PROGRAMS", "programs")
        tree.add("OPT", "opt")
        tree.add("CP2K", "cp2k")
        tree.add("PROPERTIES", "properties")

        tree.add("DLPOLY", "dlpoly")
        tree.add("GJF", "dlpoly_gjf", parent="dlpoly")

        tree.add(".DATA", "data")
        tree.add("data", "data_file", parent="data")

        tree.add("JOBS", "jobs", parent="data")
        tree.add("jid", "jid", parent="jobs")
        tree.add("DATAFILES", "datafiles", parent="jobs")

        tree.add("ADAPTIVE_SAMPLING", "adaptive_sampling", parent="data")
        tree.add("alpha", "alpha", parent="adaptive_sampling")
        tree.add("cv_errors", "cv_errors", parent="adaptive_sampling")

        tree.add("PROPERTIES", "properties_daemon", parent="adaptive_sampling")
        tree.add("properties.pid", "properties_pid", parent="properties_daemon")
        tree.add("properties.out", "properties_stdout", parent="properties_daemon")
        tree.add("properties.err", "properties_stderr", parent="properties_daemon")

        tree.add("FILES_REMOVED", "file_remover_daemon", parent="data")
        tree.add("file_remover.pid", "file_remover_pid", parent="file_remover_daemon")
        tree.add(
            "file_remover.out", "file_remover_stdout", parent="file_remover_daemon"
        )
        tree.add(
            "file_remover.err", "file_remover_stderr", parent="file_remover_daemon"
        )

        tree.add("SCRIPTS", "scripts", parent="data")
        tree.add("OUTPUTS", "outputs", parent="scripts")
        tree.add("ERRORS", "errors", parent="scripts")

        return tree

    @staticmethod
    def get_filetype(fname, return_dot=True):
        return os.path.splitext(fname)[1][int(not return_dot) :]

    @staticmethod
    def get_files_in(directory, pattern, sort="normal"):
        files = glob(os.path.join(directory, pattern))
        if sort.lower() == "normal":
            return sorted(files)
        elif sort.lower() == "natural":
            return UsefulTools.natural_sort(files)
        else:
            return files

    @staticmethod
    def get_basename(fname, return_extension=False):
        basename = os.path.basename(fname)
        if return_extension:
            return basename
        else:
            return os.path.splitext(basename)[0]

    @staticmethod
    def move_file(src, dst):
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        shutil.move(src, dst)

    @staticmethod
    def copy_file(src, dst):
        if os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
        shutil.copy(src, dst)

    @staticmethod
    def end_name(path):
        return os.path.basename(os.path.normpath(path))

    @staticmethod
    def check_directory(directory):
        if not os.path.isdir(directory):
            print(f"Error: {directory} does not exist.")
            quit()
        # Check if there are files in the directory
        filetypes = [".gjf", ".wfn", ".int"]
        for f in FileTools.get_files_in(directory, "*.*"):
            if FileTools.get_filetype(f) in filetypes:
                basename = os.path.join(directory, FileTools.get_basename(f))
                if not os.path.isdir(basename):
                    os.mkdir(basename)
                FileTools.move_file(f, basename)

    @staticmethod
    def rmtree(directory):
        if os.path.isdir(directory):
            shutil.rmtree(directory)

    @staticmethod
    def mkdir(directory, empty=False):
        if os.path.isdir(directory) and empty:
            shutil.rmtree(directory)
        os.makedirs(directory, exist_ok=True)

    @staticmethod
    def count_points_in(directory):
        FileTools.check_directory(directory)

        def gjf_in(l):
            return any(f.endswith(".gjf") for f in l)

        num_points = 0
        for d in os.walk(directory):
            num_points += 1 if gjf_in(d[2]) else 0
        return num_points

    @staticmethod
    def end_of_path(path):
        if path.endswith(os.sep):
            path = path.rstrip(os.sep)
        return os.path.split(path)[-1]

    @staticmethod
    def write_to_file(data, file=None):
        if file is None:
            file = "data_file"

        file = GLOBALS.FILE_STRUCTURE[file]
        FileTools.mkdir(os.path.dirname(file))

        with open(file, "w") as f:
            for line in data:
                f.write(f"{line}\n")

    @staticmethod
    def get_first_gjf(directory):
        for f in FileTools.get_files_in(directory, "*"):
            if f.endswith(".gjf"):
                return f
            elif os.path.isdir(f):
                f = FileTools.get_first_gjf(f)
                if f is not None:
                    return f
        return None

    @staticmethod
    def count_models(directory):
        return sum(
            1
            for model_dir in FileTools.get_files_in(directory, "*/")
            if len(FileTools.get_files_in(model_dir, "*_kriging_*.txt")) > 0
        )

    @staticmethod
    def get_opt(required=False):
        def no_opt_found():
            print(f"Error: {opt_dir} not found")
            print()
            print("No Optimised Geometry Found")
            if UsefulTools.check_bool(
                input("Would you like to calculate the optimum geometry? [Y/N]")
            ):
                print("Performing Geometry Optimisation")
                print("Continue Analysis Once Completed")
                print()
                opt()
                print("Exiting...")
            quit()

        opt_dir = GLOBALS.FILE_STRUCTURE["opt"]
        if not os.path.isdir(opt_dir) and required:
            no_opt_found()
        opt = Point(opt_dir)
        opt.find_wfn()
        if opt.wfn:
            return opt.wfn
        elif required:
            no_opt_found()

    @staticmethod
    def clear_script_outputs(outputs=True, errors=True):
        if outputs:
            FileTools.rmtree(GLOBALS.FILE_STRUCTURE["outputs"])
        if errors:
            FileTools.rmtree(GLOBALS.FILE_STRUCTURE["errors"])

    @staticmethod
    def copymodels(src, dst, symlinks=False, ignore=None):
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            try:
                if os.path.isdir(s):
                    shutil.copytree(s, d, symlinks, ignore)
                else:
                    shutil.copy2(s, d)
            except:
                FileTools.copymodels(s, d, symlinks, ignore)

    @staticmethod
    @lru_cache()
    def get_extension(path):
        return os.path.splitext(path)[1]


class my_tqdm:
    """
    Decorate an iterable object, returning an iterator which acts exactly
    like the original iterable.

    Used to replace tqdm when not writing to std.out, prevents ugly
    output files, should function identically while doing nothing
    """

    def __new__(cls, *args, **kwargs):
        # Create a new instance
        instance = object.__new__(cls)
        return instance

    def __init__(
        self,
        iterable=None,
        desc=None,
        total=None,
        leave=True,
        file=None,
        ncols=None,
        mininterval=0.1,
        maxinterval=10.0,
        miniters=None,
        ascii=None,
        disable=False,
        unit="it",
        unit_scale=False,
        dynamic_ncols=False,
        smoothing=0.3,
        bar_format=None,
        initial=0,
        position=None,
        postfix=None,
        unit_divisor=1000,
        write_bytes=None,
        lock_args=None,
        gui=False,
        **kwargs,
    ):

        # Store the arguments
        self.iterable = iterable
        self.desc = desc or ""
        self.total = total
        self.leave = leave
        self.fp = file
        self.ncols = ncols
        self.mininterval = mininterval
        self.maxinterval = maxinterval
        self.miniters = miniters
        self.ascii = ascii
        self.disable = disable
        self.unit = unit
        self.unit_scale = unit_scale
        self.unit_divisor = unit_divisor
        self.lock_args = lock_args
        self.gui = gui
        self.dynamic_ncols = dynamic_ncols
        self.bar_format = bar_format
        self.postfix = None

        # Init the iterations counters
        self.last_print_n = initial
        self.n = initial

        self.pos = 0

    def __bool__(self):
        if self.total is not None:
            return self.total > 0
        return bool(self.iterable)

    def __nonzero__(self):
        return self.__bool__()

    def __len__(self):
        return 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    def clear(self, nolock=False):
        pass

    def refresh(self, nolock=False, lock_args=None):
        pass

    def unpause(self):
        pass

    def reset(self, total=None):
        pass

    def set_description(self, desc=None, refresh=True):
        pass

    def set_description_str(self, desc=None, refresh=True):
        pass

    def set_postfix(self, ordered_dict=None, refresh=True, **kwargs):
        pass

    def set_postfix_str(self, s="", refresh=True):
        pass

    def moveto(self, n):
        pass

    def update(self):
        pass

    @property
    def format_dict(self):
        pass

    def display(self, msg=None, pos=None):
        pass

    def __hash__(self):
        return id(self)

    def __iter__(self):
        # Inlining instance variables as locals (speed optimisation)
        iterable = self.iterable
        yield from iterable


class FerebusTools:
    @staticmethod
    def write_finput(
        directory,
        natoms,
        atom,
        training_set_size,
        predictions=0,
        nproperties=1,
        optimization="pso",
    ):
        finput_fname = os.path.join(directory, "FINPUT.txt")
        atom_num = re.findall("\d+", atom)[0]

        starting_properties = 1

        with open(finput_fname, "w+") as finput:
            finput.write(f"{GLOBALS.SYSTEM_NAME}\n")
            finput.write(f"natoms {natoms}\n")
            finput.write(f"starting_properties {starting_properties} \n")
            finput.write(f"nproperties {nproperties}\n")
            finput.write(
                "#\n# Training set size and definition of reduced training set size\n#\n"
            )
            finput.write(f"full_training_set {training_set_size}\n")
            finput.write(
                "#\n# Prediction number and definition of new predictions\n#\n"
            )
            finput.write(f"predictions {predictions}\n")
            if "py" in str(GLOBALS.FEREBUS_VERSION):
                finput.write(f"kernel {GLOBALS.KERNEL}\n")
            finput.write(
                "#\nfeatures_number 0        # if your are kriging only one atom or you don't want to use he standard "
                "calculation of the number of features based on DOF of your system. Leave 0 otherwise\n#\n"
            )
            if GLOBALS.NORMALISE:
                finput.write("norm\n")
            elif GLOBALS.STANDARDISE:
                finput.write("stand\n")
            line_break = "~" * 97

            finput.write(f"#\n#{line_break}\n")

            finput.write("# Optimizers parameters\n#\n")
            finput.write("redo_weights n\n")
            finput.write("dynamical_selection n\n")
            finput.write(
                f"optimization {optimization}          "
                "# choose between DE (Differential Evolution) "
                "and PSO (Particle Swarm Optimization)\n"
            )
            finput.write(
                "fix P                    "
                "# P = fixed p) T = fixed Theta (valid only for BFGS)) "
                "N = nothing (i.e. optimization theta/p)\n"
            )
            finput.write(
                "p_value        2.00      # if no p optimization is used p_value MUST be inserted\n"
            )
            finput.write(
                f"theta_max            {GLOBALS.FEREBUS_MAX_THETA}          "
                "# select maximum value of theta for initialization "
                "(Raise if receiving an error with Theta Values)\n"
            )
            finput.write(
                f"theta_min            {GLOBALS.FEREBUS_MIN_THETA}   # select maximum value of theta for initialization\n"
            )
            finput.write(f"nugget            {GLOBALS.FEREBUS_NUGGET}\n")
            finput.write(
                "noise_specifier  n       "
                "# answer yes (Y) to allow noise optimization, "
                "no (N) to use no-noise option\n"
            )
            finput.write("noise_value 0.1\n")
            finput.write(f"tolerance        {GLOBALS.FEREBUS_TOLERANCE}#\n")
            finput.write(f"convergence      {GLOBALS.FEREBUS_CONVERGENCE}#\n")
            finput.write(f"max_iterations   {GLOBALS.FEREBUS_MAX_ITERATION}#\n")
            finput.write(f"#\n#{line_break}\n")

            finput.write("# PSO Specific keywords\n#\n")
            if GLOBALS.FEREBUS_SWARM_SIZE < 0:
                finput.write("swarm_specifier  D       ")
            else:
                finput.write("swarm_specifier  S       ")
            finput.write(
                "swarm_specifier  D       "
                "# answer dynamic (D) or static "
                "(S) as option for swarm optimization\n"
            )
            if GLOBALS.FEREBUS_SWARM_SIZE < 0:
                finput.write(f"swarm_pop     1440       ")
            else:
                finput.write(f"swarm_pop    {GLOBALS.FEREBUS_SWARM_SIZE}       ")
            finput.write(
                "# if swarm opt is set as 'static' the number of particle must be specified\n"
            )
            finput.write("cognitive_learning   1.49400\n")
            finput.write("inertia_weight   0.72900\n")
            finput.write("social_learning   1.49400\n")
            finput.write(f"#\n#{line_break}\n")

            finput.write("# DE Specific keyword\n#\n")
            finput.write("population_size 8\n")
            finput.write("mutation_strategy 4\n")
            finput.write("population_reduction n\n")
            finput.write(
                "reduction_start 5        # the ratio convergence/reduction_start < 5\n"
            )
            finput.write(f"#\n#{line_break}\n")

            finput.write("# bfgs specific keywords\n#\n")
            finput.write(
                "projg_tol 1.0d-2 # The iteration will stop when max{|proj g_i | i = 1, ...,n} <= projg_tol\n"
            )
            finput.write(
                "grad_tol 1.0d-7 # The iteration will stop when | proj g |/(1 + |f(x)|) <=grad_tol\n"
            )
            finput.write(
                "factor 1.0d+7 "
                "# The iteration will stop when (f(x)^k -f(x)^{k+1})/max{|f(x)^k|,|f(x)^{k+1}|,1} "
                "<= factor*epsmch\n"
            )
            finput.write(
                "#                     Typical values for factr: 1.d+12 for low accuracy) 1.d+7\n"
            )
            finput.write(
                "#                     for moderate accuracy) 1.d+1 for extremely high accuracy\n#\n"
            )
            finput.write(
                "iprint 101 # It controls the frequency and type of output generated:\n"
            )
            finput.write("#                     iprint<0    no output is generated)\n")
            finput.write(
                "#                     iprint=0    print only one line at the last iteration)\n"
            )
            finput.write(
                "#                     0<iprint<99 print also f and |proj g| every iprint iterations)\n"
            )
            finput.write(
                "#                     iprint=99   print details of every iteration except n-vectors)\n"
            )
            finput.write(
                "#                     iprint=100  print also the changes of active set and final x)\n"
            )
            finput.write(
                "#                     iprint>100  print details of every iteration including x and grad)\n"
            )
            finput.write(
                "#                     when iprint > 0 iterate.dat will be created\n"
            )
            finput.write(f"#\n#{line_break}\n")

            finput.write("# Atoms type and index\n#\n")
            finput.write(
                "atoms                      "
                "# this keyword tells the program than the next lines are the index number and atom type\n"
            )
            finput.write(f"{atom_num}   {atom}\n")


class Problem:
    def __init__(self, name="", problem="", solution=""):
        self.name = name
        self.problem = problem
        self.solution = solution

    def __str__(self):
        return (
            f"Problem:     {self.name}\n"
            f"Description: {self.problem}\n"
            f"Solution:    {self.solution}"
        )

    def __repr__(self):
        return str(self)


class ProblemFinder:
    unknown_settings = []

    def __init__(self):
        self.problems = []

    @UsefulTools.run_function(1)
    def check_alf(self):
        if len(GLOBALS.ALF) < 1:
            self.add(
                Problem(
                    name="ALF",
                    problem="ALF not set due to error in calculation",
                    solution="Set 'ALF_REFERENCE_FILE' or manually set 'ALF' in config file",
                )
            )

    @UsefulTools.run_function(2)
    def check_directories(self):
        dirs_to_check = ["training_set", "sample_pool"]

        for dir_name in dirs_to_check:
            dir_path = GLOBALS.FILE_STRUCTURE[dir_name]
            if not os.path.isdir(dir_path):
                self.add(
                    Problem(
                        name="Directory Not Found",
                        problem=f"Could not find: {dir_path}",
                        solution="Setup directory structure or create manually",
                    )
                )

    @UsefulTools.run_function(3)
    def check_system(self):
        if GLOBALS.SYSTEM_NAME == "SYSTEM":
            self.add(
                Problem(
                    name="SYSTEM_NAME",
                    problem="SYSTEM_NAME not been set, defaulted to SYSTEM",
                    solution="Set 'SYSTEM_NAME' in config file",
                )
            )

    @UsefulTools.run_function(4)
    def check_settings(self):
        for setting in ProblemFinder.unknown_settings:
            self.add(
                Problem(
                    name=f"Unknown setting found in config",
                    problem=f"Unknown setting: {setting}",
                    solution="See documentation or check [o]ptions [settings] for full list of settings",
                )
            )

    def add(self, problem):
        self.problems.append(problem)

    def find(self):
        if not GLOBALS.DISABLE_PROBLEMS:
            problems_to_find = UsefulTools.get_functions_to_run(self)
            for find_problem in problems_to_find:
                find_problem()

    def __getitem__(self, i):
        return self.problems[i]

    def __len__(self):
        return len(self.problems)

    def __str__(self):
        return "\n\n".join([str(problem) for problem in self.problems])

    def __repr__(self):
        return str(self)


# ========================#
#     Cluster Tools      #
# ========================#


class Modules:
    def __init__(self):
        self._modules = {}

    @property
    def machines(self):
        return self._modules.keys()

    def __getitem__(self, machine):
        return self._modules[machine] if machine in self.machines else []

    def __setitem__(self, machine, module):
        if machine not in self.machines:
            self._modules[machine] = []
        if isinstance(module, str):
            module = [module]
        self._modules[machine] += module

    def __repr__(self):
        return repr(self._modules)


class ParallelEnvironment:
    def __init__(self, name, min_cores, max_cores):
        self.name = name
        self.min = min_cores
        self.max = max_cores


class MachineParallelEnvironments:
    def __init__(self):
        self._environments = []

    def __getitem__(self, ncores):
        for environment in self._environments:
            if environment.min <= ncores <= environment.max:
                return environment.name
        return ""

    def __add__(self, parallel_environment):
        if isinstance(parallel_environment, ParallelEnvironment):
            self._environments += [parallel_environment]
        return self


class ParallelEnvironments:
    def __init__(self):
        self._environments = {}

    @property
    def machines(self):
        return self._environments.keys()

    def __getitem__(self, machine):
        return self._environments[machine]

    def __setitem__(self, machine, environments):
        if machine not in self.machines:
            self._environments[machine] = MachineParallelEnvironments()

        if not isinstance(environments, list):
            environments = [environments]
        for parallel_environment in environments:
            if isinstance(parallel_environment, tuple):
                environment = ParallelEnvironment(*parallel_environment)
            self._environments[machine] += environment


class TimingManager:
    def __init__(self, submission_script, message=None):
        self.submission_script = submission_script
        self.message = message

    def __enter__(self):
        python_job = PythonCommand()
        if self.message:
            python_job.run_func("log_time", f"START:{self.submission_script.fname}", self.message)
        else:
            python_job.run_func("log_time", f"START:{self.submission_script.fname}")
        self.submission_script.add(python_job)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        python_job = PythonCommand()
        python_job.run_func("log_time", f"FINISH:{self.submission_script.fname}")
        self.submission_script.add(python_job)


class CommandLine:
    def __init__(self):
        self.command = ""
        self.options = []
        self.arguments = []
        self.ncores = 1

        self.modules = Modules()

        self.var_names = []
        self.array_names = []

        self.datafile = None
        self.datasources = []

        self.setup()

    def setup(self):
        self.load_modules()
        self.setup_options()
        self.setup_arguments()
        self.setup_command()

    def setup_datafile(self):
        if GLOBALS.UID is None:
            UsefulTools.set_uid()
        self.datafile = str(GLOBALS.UID)

    def setup_command(self):
        if (
            hasattr(self, "machine_commands")
            and str(GLOBALS.MACHINE).lower() in self.machine_commands.keys()
        ):
            self.command = self.machine_commands[str(GLOBALS.MACHINE).lower()]
        elif hasattr(self, "default_command"):
            self.command = self.default_command

    def setup_array_names(self, ndata=None):
        if not ndata:
            ndata = self.ndata
        return [f"arr{i+1}" for i in range(ndata)]

    def setup_var_names(self, ndata=None):
        if not ndata:
            ndata = self.ndata
        return [f"var{i+1}" for i in range(ndata)]

    def get_variable(self, index, var="SGE_TASK_ID-1"):
        if len(self) > 1 or _data_lock:
            if not self.array_names:
                self.array_names = self.setup_array_names()
            if isinstance(var, int):
                return f"${{{self.array_names[index]}[${self.var_names[var]}]}}"
            else:
                return f"${{{self.array_names[index]}[${var}]}}"
        else:
            return self.datasources[index][0]
        return ""

    def setup_options(self):
        pass

    def setup_arguments(self):
        pass

    def load_modules(self):
        pass

    def create_outfile(self, infile, ext="log"):
        return os.path.splitext(infile)[0] + f".{ext}"

    def _read_data_file_string(self, datafile, data, delimiter=","):
        if len(self) == 1 and not _data_lock:
            return ""

        datafile = os.path.abspath(datafile)

        self.array_names = self.setup_array_names(len(data))
        self.var_names = self.setup_var_names(len(data))

        read_data_file = [f"file={datafile}", ""]
        for array_name in self.array_names:
            read_data_file += [f"{array_name}=()"]
        read_data_file += [
            f"while IFS={delimiter} read -r " + " ".join(self.var_names),
            "do",
        ]
        for array_name, var_name in zip(self.array_names, self.var_names):
            read_data_file += [f"    {array_name}+=(${var_name})"]
        read_data_file += ["done < $file"]
        return "\n".join(read_data_file) + "\n"

    def _write_data_file(self, fname, data, delimiter=","):
        if _data_lock:
            return
        with open(fname, "w") as f:
            for data_line in zip(*data):
                if isinstance(data_line, (list, tuple)):
                    data_line = delimiter.join(data_line)
                f.write(f"{data_line}\n")

    def setup_data_file(self, fname, *data, delimiter=","):
        self.datasources = data
        FileTools.mkdir(GLOBALS.FILE_STRUCTURE["datafiles"])
        if os.path.dirname != GLOBALS.FILE_STRUCTURE["datafiles"]:
            fname = os.path.join(
                GLOBALS.FILE_STRUCTURE["datafiles"], os.path.basename(fname)
            )
        self._write_data_file(fname, data, delimiter)
        datafile_string = self._read_data_file_string(fname, data, delimiter)
        UsefulTools.set_uid()  # make new uid after using
        return datafile_string

    @property
    def ndata(self):
        return 1

    def __repr__(self):
        self.tokens = [self.command] + self.arguments
        return " ".join(self.tokens)

    def __len__(self):
        if hasattr(self, "njobs"):
            return self.njobs
        elif hasattr(self, "infiles"):
            return len(self.infiles)
        else:
            return 1


class GaussianCommand(CommandLine):
    def __init__(self):
        self.infiles = []
        self.outfiles = []

        self.default_command = "g09"
        self.machine_commands = {"csf3": "$g09root/g09/g09", "ffluxlab": "g09"}

        super().__init__()

        self.setup_datafile()
        self.ncores = GLOBALS.GAUSSIAN_CORE_COUNT

    @property
    def njobs(self):
        return len(self.infiles)

    def add(self, gjf_file, outfile=None):
        self.infiles += [gjf_file]
        self.outfiles += (
            [self.create_outfile(gjf_file, ext="gau")] if not outfile else [outfile]
        )

    def load_modules(self):
        self.modules["csf3"] = ["apps/binapps/gaussian/g09d01_em64t"]
        self.modules["ffluxlab"] = ["apps/gaussian/g09"]

    @property
    def ndata(self):
        return 2

    def __repr__(self):
        if len(self.infiles) < 1:
            return ""

        datafile = self.setup_data_file(self.datafile, self.infiles, self.outfiles)
        infile = self.get_variable(0)
        outfile = self.get_variable(1)

        runcmd = " ".join([self.command, infile, outfile])
        return datafile + "\n" + runcmd


class AIMAllCommand(CommandLine):
    def __init__(self):
        self.infiles = []
        self.outfiles = []

        self.default_command = "~/AIMAll/aimqb.ish"
        self.machine_commands = {
            "csf3": "~/AIMAll/aimqb.ish",
            "ffluxlab": "aimall",
        }

        super().__init__()

        self.setup_datafile()
        self.ncores = GLOBALS.AIMALL_CORE_COUNT
        self.setup_arguments()

    def add(self, wfn_file, outfile=None):
        self.infiles += [wfn_file]
        self.outfiles += (
            [self.create_outfile(wfn_file, ext="aim")] if not outfile else [outfile]
        )

    def load_modules(self):
        self.modules["ffluxlab"] = ["apps/aimall/17.11.14"]

    def setup_options(self):
        self.options = ["-j y", "-S /bin/bash"]

    def setup_arguments(self):
        self.arguments = [
            "-nogui",
            "-usetwoe=0",
            "-atom=all",
            f"-encomp={GLOBALS.ENCOMP}",
            f"-boaq={GLOBALS.BOAQ}",
            f"-iasmesh={GLOBALS.IASMESH}",
            f"-nproc={self.ncores}",
            f"-naat={self.ncores}",
        ]

    @property
    def ndata(self):
        return 2

    def __repr__(self):
        if len(self.infiles) < 1:
            return ""

        datafile = self.setup_data_file(self.datafile, self.infiles, self.outfiles)
        infile = self.get_variable(0)
        outfile = self.get_variable(1)

        runcmd = [self.command, *self.arguments, infile, "&>", outfile]
        runcmd = " ".join(runcmd)
        return datafile + "\n" + runcmd


class FerebusCommand(CommandLine):
    def __init__(self):
        self.directories = []

        super().__init__()

        self.setup_datafile()
        self.ncores = GLOBALS.FEREBUS_CORE_COUNT

    def setup_command(self):
        ferebus_loc = os.path.abspath(str(GLOBALS.FEREBUS_LOCATION))
        if "py" in str(GLOBALS.FEREBUS_VERSION):
            ferebus_loc += ".py" if not ferebus_loc.endswith(".py") else ""
            self.command = "python " + ferebus_loc
        else:
            self.command = ferebus_loc

    def add(self, directory):
        self.directories += [os.path.abspath(directory)]

    def load_modules(self):
        if "py" not in str(GLOBALS.FEREBUS_VERSION):
            self.modules["ffluxlab"] = [
                "mpi/intel/18.0.3",
                "libs/nag/intel/fortran/mark-23",
            ]
            self.modules["csf3"] = [
                "compilers/intel/17.0.7",
                "libs/intel/nag/fortran_mark23_intel",
            ]
        self.modules["csf3"] += ["apps/anaconda3/5.2.0/bin"]

    @property
    def ndata(self):
        return 1

    def __repr__(self):
        if len(self.directories) < 1:
            return ""

        datafile = ""
        datafile = self.setup_data_file(self.datafile, self.directories)
        directory = self.get_variable(0)

        runcmd = [f"pushd {directory}", self.command, "popd"]
        runcmd = "\n".join(runcmd)
        return datafile + "\n" + runcmd

    def __len__(self):
        return len(self.directories)


class DlpolyCommand(CommandLine):
    def __init__(self):
        self.directories = []

        super().__init__()

        self.setup_datafile()
        self.ncores = GLOBALS.DLPOLY_CORE_COUNT

    def setup_command(self):
        self.command = os.path.abspath(str(GLOBALS.DLPOLY_LOCATION))

    def add(self, directory):
        self.directories += [os.path.abspath(directory)]

    def load_modules(self):
        self.modules["ffluxlab"] = ["compilers/gcc/8.2.0"]
        self.modules["csf3"] = ["compilers/gcc/8.2.0"]

    @property
    def ndata(self):
        return 1

    def __repr__(self):
        if len(self.directories) < 1:
            return ""

        datafile = ""
        datafile = self.setup_data_file(self.datafile, self.directories)
        directory = self.get_variable(0)

        runcmd = [f"pushd {directory}", self.command, "popd"]
        runcmd = "\n".join(runcmd)
        return datafile + "\n" + runcmd

    def __len__(self):
        return len(self.directories)


class PythonCommand(CommandLine):
    def __init__(self, py_file=None):
        self.py_script = __file__ if not py_file else py_file
        self.default_command = "python"
        super().__init__()
        self.add_argument("-u", str(GLOBALS.UID))
        self.add_argument("-c", str(Arguments.config_file))

    def load_modules(self):
        self.modules["csf3"] = ["apps/anaconda3/5.2.0/bin"]

    def add_argument(self, arg, val=None):
        self.arguments += [arg]
        if val:
            self.arguments += [val]

    def run_func(self, function_name, *args):
        args = [str(arg) for arg in args]
        self.arguments += ["-f", f"{function_name}", *args]

    def __repr__(self):
        runcmd = [self.command, self.py_script, " ".join(self.arguments)]
        return " ".join(runcmd)


class SubmissionScript:
    def __init__(self, fname, directory=None):
        self.fname = fname
        self._commands = []
        self._modules = []
        self.parallel_environments = ParallelEnvironments()

        self.stdout = GLOBALS.FILE_STRUCTURE["outputs"]
        self.stderr = GLOBALS.FILE_STRUCTURE["errors"]

        self.directory = directory
        if not self.directory:
            self.directory = GLOBALS.FILE_STRUCTURE["scripts"]

    def add(self, command):
        self._commands.append(command)

    def load_modules(self):
        for command in self:
            self._modules += command.modules[str(GLOBALS.MACHINE)]

    def cleanup_modules(self):
        self._modules = list(set(self._modules))

    def cleanup(self):
        self.cleanup_modules()

    def setup_pe(self):
        self.parallel_environments["ffluxlab"] = [("smp", 2, 64)]
        self.parallel_environments["csf3"] = [("smp.pe", 2, 32)]
        self.parallel_environments["local"] = [("", 2, mp.cpu_count())]

    def setup_stdout(self):
        FileTools.mkdir(self.stdout)
        FileTools.mkdir(self.stderr)

    def setup(self):
        self.setup_pe()
        self.load_modules()
        self.setup_stdout()

    def node_options(self):
        node_options = []

        include_nodes = "|".join(GLOBALS.INCLUDE_NODES)
        exclude_nodes = "|".join(GLOBALS.EXCLUDE_NODES)

        if include_nodes:
            node_options += [f"({include_nodes})"]
        if exclude_nodes:
            node_options += [f"!({exclude_nodes})"]

        return (
            "#$ -l h=" + "&".join(node_options) + "\n" if len(node_options) > 0 else ""
        )

    def check_task_id(self):
        check_task_str = [
            'if [ "$SGE_TASK_ID" = "undefined" ]; then',
            "    SGE_TASK_ID=1",
            "fi",
        ]
        return "\n".join(check_task_str)

    def write(self):
        self.setup()
        self.cleanup()

        FileTools.mkdir(self.directory)
        self.fname = os.path.join(self.directory, self.fname)

        njobs = ""
        if self.njobs > 1:
            njobs = f"-{self.njobs}"

        with open(self.fname, "w") as f:
            f.write("#!/bin/bash -l\n")
            f.write("#$ -cwd\n")
            f.write(f"#$ -o {self.stdout}\n")
            f.write(f"#$ -e {self.stderr}\n")
            for option in self.options:
                f.write(f"#$ {option}\n")

            f.write(self.node_options())

            pe = self.parallel_environments[str(GLOBALS.MACHINE)][self.ncores]
            if self.ncores > 1:
                f.write(f"#$ -pe {pe} {self.ncores}\n")

            if self.njobs > 1:
                f.write(f"#$ -t 1{njobs}\n")
            else:
                f.write(f"\n{self.check_task_id()}\n")

            f.write("\n")

            for module in self._modules:
                f.write(f"module load {module}\n")

            if self.ncores > 1:
                f.write("export OMP_NUM_THREADS=$NSLOTS\n\n")

            f.write("\n")
            for command in self._commands:
                f.write(f"{repr(command)}\n")

    def submit(self, hold=None):
        return BatchTools.qsub(self.fname, hold)

    @property
    def ncores(self):
        return max(command.ncores for command in self)

    @property
    def options(self):
        options = []
        for command in self:
            options += command.options
        return options

    @property
    def njobs(self):
        return max(len(command) for command in self)

    def __getitem__(self, i):
        return self._commands[i]


class SubmissionTools:
    @staticmethod
    def make_g09_script(points, directory="", redo=False, submit=True, hold=None):
        gaussian_job = GaussianCommand()
        if isinstance(points, Points):
            for point in points:
                if (
                    point.gjf and (redo or not os.path.exists(point.gjf.wfn.path))
                ) or isinstance(point, MockDirectory):
                    gaussian_job.add(point.gjf.path)
        elif isinstance(points, GJF):
            gaussian_job.add(points.path)

        script_name = os.path.join(directory, "GaussSub.sh")
        submission_script = SubmissionScript(script_name)
        with TimingManager(submission_script):
            submission_script.add(gaussian_job)
        submission_script.write()

        jid = None
        if submit:
            jid = submission_script.submit(hold=hold)
        return submission_script.fname, jid

    @staticmethod
    def make_aim_script(
        points, directory="", check_wfns=True, redo=False, submit=True, hold=None,
    ):
        if check_wfns:
            result = points.check_wfns()
            if result is not None:
                _, jid = AutoTools.submit_ichor_wfns(result[1], directory=points.path)
                return AutoTools.submit_wfns(jid, len(points))

        aimall_job = AIMAllCommand()
        for point in points:
            if (
                point.wfn
                and (redo or not point.wfn.aimall_complete)
                or isinstance(point, MockDirectory)
            ):
                aimall_job.add(point.wfn.path)
            elif point.gjf and not check_wfns:
                aimall_job.add(point.gjf.wfn.path)

        script_name = os.path.join(directory, "AIMSub.sh")
        submission_script = SubmissionScript(script_name)
        with TimingManager(submission_script):
            submission_script.add(aimall_job)
        submission_script.write()

        jid = None
        if submit:
            jid = submission_script.submit(hold=hold)
        return submission_script.fname, jid

    @staticmethod
    def make_ferebus_script(
        model_directories, directory="", submit=True, hold=None, model_type="iqa",
    ):
        ferebus_job = FerebusCommand()
        for model_directory in model_directories:
            ferebus_job.add(model_directory)

        move_models = PythonCommand()
        move_models.run_func("move_models", ferebus_job.get_variable(0), model_type)

        script_name = os.path.join(directory, "FereSub.sh")
        submission_script = SubmissionScript(script_name)
        with TimingManager(submission_script):
            submission_script.add(ferebus_job)
            submission_script.add(move_models)
        submission_script.write()

        jid = None
        if submit:
            jid = submission_script.submit(hold=hold)
        return submission_script.fname, jid

    @staticmethod
    def make_python_script(
        python_script, directory="", function="", args=(), submit=True, hold=None,
    ):
        python_job = PythonCommand()
        if function:
            python_job.run_func(function, *args)

        script_name = os.path.join(directory, "PySub.sh")
        submission_script = SubmissionScript(script_name)
        with TimingManager(submission_script, function):
            submission_script.add(python_job)
        submission_script.write()

        jid = None
        if submit:
            jid = submission_script.submit(hold=hold)
        return submission_script.fname, jid

    @staticmethod
    def make_dlpoly_script(dlpoly_directories, directory="", submit=True, hold=None):
        dlpoly_job = DlpolyCommand()
        for dlpoly_directory in dlpoly_directories:
            dlpoly_job.add(dlpoly_directory)

        script_name = os.path.join(directory, "DlpolySub.sh")
        submission_script = SubmissionScript(script_name)
        submission_script.add(dlpoly_job)
        submission_script.write()

        jid = None
        if submit:
            jid = submission_script.submit(hold=hold)
        return submission_script.fname, jid


class BatchTools:
    @staticmethod
    def _read_jids(jid_file):
        with open(jid_file, "r") as f:
            jids = f.readlines()
        return [jid.strip() for jid in jids]

    @staticmethod
    def _cleanup_jids(jid_file):
        submitted_jobs = BatchTools._read_jids(jid_file)
        running_jobs = BatchTools.qstat(quiet=True)
        keep_jobs = []
        for jid in submitted_jobs:
            if jid.strip() in running_jobs:
                keep_jobs.append(jid.strip())
        with open(jid_file, "w") as f:
            for jid in keep_jobs:
                f.write(f"{jid}\n")

    @staticmethod
    def _environ(context):
        return dict(os.environ)

    @staticmethod
    def run_cmd(cmd):
        E = BatchTools._environ("grid")
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=E
        )
        (stdout, stderr) = p.communicate()
        return stdout.decode("ascii").strip()

    @staticmethod
    def parse_tasks(job_line):
        tasks = []
        if "-" in job_line["ja-task-ID"]:
            task_ids = re.findall(r"\d+", job_line["ja-task-ID"])
            for _ in range(int(task_ids[0]), int(task_ids[1]) + 1):
                tasks.append(SGE_Task(job_line["state"], job_line["slots"]))
        else:
            tasks.append(SGE_Task(job_line["state"], job_line["slots"]))
        return tasks

    @staticmethod
    def qstat(quiet=False):
        output = BatchTools.run_cmd(["qstat"])
        headers, widths = [], []
        jobs = SGE_Jobs()
        job_line = {}
        job = SGE_Job("", "")

        jid_fname = GLOBALS.FILE_STRUCTURE["jid"]
        submitted_jobs = BatchTools._read_jids(jid_fname)

        for line in output.split("\n"):
            if line.startswith("-") or not line.strip():
                continue
            if not headers:
                widths = UsefulTools.get_widths(line, ignore_chars=["a"])
                headers = UsefulTools.split_widths(line, widths, strip=True)
            else:
                for header, column in zip(
                    headers, UsefulTools.split_widths(line, widths)
                ):
                    job_line[header] = column.strip()
                if job_line["job-ID"] != job.jid:
                    if job and job.jid in submitted_jobs:
                        jobs.add_job(job)
                    job = SGE_Job(job_line["name"], job_line["job-ID"])
                for task in BatchTools.parse_tasks(job_line):
                    job.add_task(task)
        if job:
            jobs.add_job(job)
        if not quiet:
            print(jobs)
        return jobs

    @staticmethod
    def qsub(script, hold=None):
        data_dir = GLOBALS.FILE_STRUCTURE["jobs"]
        FileTools.mkdir(data_dir)
        jid_fname = GLOBALS.FILE_STRUCTURE["jid"]
        with open(jid_fname, "a") as jid_file:
            qsub_cmd = []
            if GLOBALS.SGE and not GLOBALS.SUBMITTED:
                qsub_cmd += ["qsub"]
                if hold:
                    qsub_cmd += ["-hold_jid", f"{hold}"]
            else:
                qsub_cmd = ["bash"]
            qsub_cmd += [script]
            if not GLOBALS.SUBMITTED and GLOBALS.SGE:
                output = BatchTools.run_cmd(qsub_cmd)
                jid = re.findall(r"\d+", output)
                if len(jid) > 0:
                    jid = jid[0]
                    jid_file.write(f"{jid}\n")
                    jid_file.close()
                    return jid

    @staticmethod
    def qdel():
        jid_fname = GLOBALS.FILE_STRUCTURE["jid"]
        BatchTools._cleanup_jids(jid_fname)
        with open(jid_fname, "r") as f:
            for jid in f:
                jid = jid.strip()
                if jid:
                    try:
                        BatchTools.run_cmd(["qdel", f"{jid}"])
                    except:
                        pass
                    print(f"Deleted job: {jid}")


class SGE_Task:
    task_counter = it.count(1)

    def __init__(self, status, cores):
        self.id = next(SGE_Task.task_counter)
        self.status = SGE_Job.STATUS[status]

    @property
    def is_running(self):
        return self.status == SGE_Job.STATUS["r"]

    @property
    def is_holding(self):
        return self.status == SGE_Job.STATUS["hqw"]

    @property
    def is_waiting(self):
        return self.status == SGE_Job.STATUS["qw"]

    def __str__(self):
        return f"Task ID: {self.id}, Status: {self.status}"

    def __repr__(self):
        return str(self)


class SGE_Job:
    STATUS = {
        "r": "RUNNING",
        "qw": "WAITING",
        "hqw": "HOLDING",
        "hRwq": "HOLDING",
        "t": "TRANSFERRING",
        "Rr": "RESUBMIT",
        "Rt": "RESUBMIT",
        "s": "SUSPENDED",
        "dr": "DELETING",
        "dt": "DELETING",
        "dRr": "DELETING",
        "dRt": "DELETING",
        "ds": "DELETING",
        "dS": "DELETING",
        "dT": "DELETING",
        "dRs": "DELETING",
        "dRS": "DELETING",
        "dRT": "DELETING",
        "Eqw": "ERROR",
        "Ehqw": "ERROR",
        "EhRqw": "ERROR",
    }

    ## SGE QUEUE STATES ###########################################################################################
    # | Pending       | pending                                        | qw                                     | #
    # | Pending       | pending, user hold                             | qw                                     | #
    # | Pending       | pending, system hold                           | hqw                                    | #
    # | Pending       | pending, user and system hold                  | hqw                                    | #
    # | Pending       | pending, user hold, re-queue                   | hRwq                                   | #
    # | Pending       | pending, system hold, re-queue                 | hRwq                                   | #
    # | Pending       | pending, user and system hold, re-queue        | hRwq                                   | #
    # | Pending       | pending, user hold                             | qw                                     | #
    # | Pending       | pending, user hold                             | qw                                     | #
    # | Running       | running                                        | r                                      | #
    # | Running       | transferring                                   | t                                      | #
    # | Running       | running, re-submit                             | Rr                                     | #
    # | Running       | transferring, re-submit                        | Rt                                     | #
    # | Suspended     | obsuspended                                    | s,  ts                                 | #
    # | Suspended     | queue suspended                                | S, tS                                  | #
    # | Suspended     | queue suspended by alarm                       | T, tT                                  | #
    # | Suspended     | allsuspended withre-submit                     | Rs,Rts,RS, RtS, RT, RtT                | #
    # | Error         | allpending states with error                   | Eqw, Ehqw, EhRqw                       | #
    # | Deleted       | all running and suspended states with deletion | dr,dt,dRr,dRt,ds, dS, dT,dRs, dRS, dRT | #
    ###############################################################################################################

    def __init__(self, name, jid):
        self.name = name
        self.jid = jid
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)

    def split(self, s):
        return str(self).split(s)

    @property
    def ntasks(self):
        return len(self)

    @property
    def is_running(self):
        return any(task.is_running for task in self)

    @property
    def is_holding(self):
        return any(task.is_holding for task in self)

    @property
    def is_waiting(self):
        return any(task.is_waiting for task in self)

    def __eq__(self, jid):
        print(self.jid, jid)
        return int(self.jid) == int(jid)

    def __len__(self):
        return len(self.tasks)

    def __getitem__(self, i):
        return self.tasks[i]

    def __bool__(self):
        return self.tasks != []

    def __str__(self):
        s = f"Job: {self.name}, ID: {self.jid}, nTasks: {self.ntasks}\n"
        task_status = ""
        skip = True
        for i, task in enumerate(self):
            if task.status != task_status or i == len(self) - 1:
                s += f"    {str(task)}\n"
                task_status = task.status
                skip = False
            elif not skip:
                s += "    ...\n"
                skip = True
        return s

    def __repr__(self):
        return str(self)


class SGE_Jobs:
    @staticmethod
    def setup():
        pass

    def __init__(self):
        self.jobs = []

    def add_job(self, job):
        self.jobs.append(job)
        SGE_Task.task_counter = it.count(1)

    def save(self):
        pass

    @property
    def njobs(self):
        return len(self)

    @property
    def n_running(self):
        return sum(1 for job in self if job.is_running)

    @property
    def n_holding(self):
        return sum(1 for job in self if job.is_holding)

    @property
    def n_waiting(self):
        return sum(1 for job in self if job.is_waiting)

    @property
    def jids(self):
        return [str(job.jid) for job in self]

    @property
    def names(self):
        return [str(job.name) for job in self]

    def __contains__(self, j):
        return str(j) in self.jids or str(j) in self.names

    def __len__(self):
        return len(self.jobs)

    def __getitem__(self, i):
        return self.jobs[i]

    def __str__(self):
        s = f"Total Jobs: {self.njobs}\n--"
        for job in self:
            if job.is_running:
                j = str(job).split("\n")
                s += "\n  ".join(j)
        s = s.rstrip(" ")
        s += "\n"
        s += f"Running: {self.n_running} job(s)\n"
        s += f"Holding: {self.n_holding} job(s)\n"
        s += f"Waiting: {self.n_waiting} job(s)\n"
        s += "\n"
        return s

    def __repr__(self):
        return str(self)


class AutoTools:
    @staticmethod
    def submit_ichor_gjfs(jid=None, directory=None):
        if not directory:
            directory = GLOBALS.FILE_STRUCTURE["training_set"]
        return AutoTools.submit_ichor("submit_gjfs", directory, submit=True, hold=jid)

    @staticmethod
    def submit_ichor_wfns(jid=None, directory=None):
        if not directory:
            directory = GLOBALS.FILE_STRUCTURE["training_set"]
        return AutoTools.submit_ichor("submit_wfns", directory, submit=True, hold=jid)

    @staticmethod
    def submit_ichor_models(jid=None, directory=None, type=None, npoints=None):
        if not directory:
            directory = GLOBALS.FILE_STRUCTURE["training_set"]
        if not type:
            type = "iqa"
        if not npoints:
            npoints = -1
        return AutoTools.submit_ichor(
            "make_models", directory, type, npoints, submit=True, hold=jid
        )

    @staticmethod
    def submit_ichor_errors(jid=None):
        sp_dir = GLOBALS.FILE_STRUCTURE["sample_pool"]
        model_dir = GLOBALS.FILE_STRUCTURE["models"]
        return AutoTools.submit_ichor(
            "calculate_errors", model_dir, sp_dir, submit=True, hold=jid
        )

    @staticmethod
    def submit_ichor_s_curves(predict_property, validation_set, models, output_file):
        return AutoTools.submit_ichor(
            "calculate_s_curves",
            predict_property,
            validation_set,
            models,
            output_file,
            submit=True,
            hold=None,
        )

    @staticmethod
    def submit_dlpoly_gjfs(jid=None):
        return AutoTools.submit_ichor(
            "calculate_gaussian_energies", submit=True, hold=jid
        )

    @staticmethod
    def submit_dlpoly_energies(jid=None):
        return AutoTools.submit_ichor("get_wfn_energies", submit=True, hold=jid)

    @staticmethod
    def submit_dlpoly_trajectories(jid=None):
        return AutoTools.submit_ichor(
            "calculate_trajectories_wfn", submit=True, hold=jid
        )

    @staticmethod
    def submit_dlpoly_trajectories_energies(jid=None):
        return AutoTools.submit_ichor("get_trajectory_energies", submit=True, hold=jid)

    @staticmethod
    def submit_dlpoly_trajectory_energies(jid=None, directory=None):
        return AutoTools.submit_ichor(
            "get_trajectory_energy", directory, submit=True, hold=jid
        )

    @staticmethod
    def submit_ichor(function, *args, submit=False, hold=None):
        return SubmissionTools.make_python_script(
            __file__, function=function, args=args, submit=submit, hold=hold
        )

    @staticmethod
    def submit_gjfs(jid=None, npoints=None):
        if npoints is None:
            npoints = GLOBALS.POINTS_PER_ITERATION
        points = MockSet(npoints)
        return points.submit_gjfs(redo=False, submit=True, hold=jid)

    @staticmethod
    def submit_wfns(jid=None, npoints=None):
        if npoints is None:
            npoints = GLOBALS.POINTS_PER_ITERATION
        points = MockSet(npoints)
        return points.submit_wfns(redo=False, submit=True, hold=jid, check_wfns=False)

    @staticmethod
    def submit_models(jid=None, directory=None):
        if not directory:
            directory = GLOBALS.FILE_STRUCTURE["training_set"]
        gjf = GJF(FileTools.get_first_gjf(directory)).read()
        return SubmissionTools.make_ferebus_script(
            gjf.atoms.atoms,
            submit=True,
            hold=jid,
            model_type=str(GLOBALS.OPTIMISE_PROPERTY),
        )

    @staticmethod
    def submit_aimall(directory=None, jid=None):
        global _data_lock
        points = Set(directory)
        npoints = len(points)
        UsefulTools.set_uid()
        _data_lock = True
        script, jid = AutoTools.submit_ichor_gjfs(jid, directory=directory)
        script, jid = AutoTools.submit_gjfs(jid, npoints)
        script, jid = AutoTools.submit_ichor_wfns(jid, directory=directory)
        AutoTools.submit_wfns(jid, npoints)
        _data_lock = False

    @staticmethod
    def run_models(directory=None, type=None, npoints=None, jid=None):
        _, jid = AutoTools.submit_ichor_models(
            jid=jid, directory=directory, type=type, npoints=npoints
        )
        return AutoTools.submit_models(jid=jid, directory=directory)

    @staticmethod
    def run_from_extern():
        Arguments.read()
        Globals.define()
        AutoTools.run()

    @staticmethod
    def run():
        global _data_lock

        FileTools.clear_log()
        FileTools.clear_script_outputs()
        UsefulTools.set_uid()

        UsefulTools.suppress_tqdm()

        GLOBALS.IQA_MODELS = str(GLOBALS.OPTIMISE_PROPERTY) == "iqa"

        order = [
            AutoTools.submit_ichor_gjfs,
            AutoTools.submit_gjfs,
            AutoTools.submit_ichor_wfns,
            AutoTools.submit_wfns,
            AutoTools.submit_ichor_models,
            AutoTools.submit_models,
            AutoTools.submit_ichor_errors,
        ]

        jid = None
        training_set = Set(GLOBALS.FILE_STRUCTURE["training_set"])
        npoints = len(training_set)

        logger.info("Starting ICHOR Auto Run")
        _data_lock = True

        for i in range(GLOBALS.MAX_ITERATION):
            for func in order:
                args = {"jid": jid}
                if i == 0 and "npoints" in func.__code__.co_varnames:
                    args["npoints"] = npoints
                if "type" in func.__code__.co_varnames:
                    args["type"] = str(GLOBALS.OPTIMISE_PROPERTY)
                script_name, jid = func(**args)
                print(f"Submitted {script_name}: {jid}")

        for func in order[:-1]:
            args = {"jid": jid}
            if "write_data" in func.__code__.co_varnames:
                args["write_data"] = False
            if "type" in func.__code__.co_varnames:
                args["type"] = str(GLOBALS.OPTIMISE_PROPERTY)
            script_name, jid = func(**args)
            print(f"Submitted {script_name}: {jid}")

        GLOBALS.SUBMITTED = False
        _data_lock = False


class PropertiesDaemon(Daemon):
    def __init__(self):
        cwd = os.getcwd()
        pidfile = os.path.join(cwd, GLOBALS.FILE_STRUCTURE["properties_pid"])
        stdout = os.path.join(cwd, GLOBALS.FILE_STRUCTURE["properties_stdout"])
        stderr = os.path.join(cwd, GLOBALS.FILE_STRUCTURE["properties_stderr"])
        super().__init__(pidfile, stdout=stdout, stderr=stderr)

    def run(self):
        PropertyTools.run()
        self.stop()


class PropertyTools:
    @staticmethod
    def run_daemon():
        FileTools.mkdir(GLOBALS.FILE_STRUCTURE["properties_daemon"], empty=True)
        properties_daemon = PropertiesDaemon()
        properties_daemon.start()

    @staticmethod
    def stop_daemon():
        properties_daemon = PropertiesDaemon()
        properties_daemon.stop()

    @staticmethod
    def check_daemon():
        properties_daemon = PropertiesDaemon()
        is_running = properties_daemon.check()
        if is_running:
            print("Run Properties background process is still running")
        else:
            print("Run Properties background process has finished")

    @staticmethod
    def run():
        original_property = GLOBALS.OPTIMISE_PROPERTY

        property_directories = []
        properties = GLOBALS.OPTIMISE_PROPERTY.allowed_values
        properties_root = GLOBALS.FILE_STRUCTURE["properties"]

        print()
        if not os.path.exists(properties_root):
            # make directory
            print(f'Making {properties_root}')
            FileTools.mkdir(properties_root, empty=False)
            print()
            # make property directories
            print("Making Property Directories")
            with tqdm(total=len(properties), unit=" dirs") as progressbar:
                for property_name in properties:
                    progressbar.set_description(property_name)

                    property_directory = os.path.join(
                        properties_root, property_name
                    )
                    FileTools.mkdir(property_directory, empty=False)
                    property_directories += [(property_name, property_directory)]

                    progressbar.update()
            print()
            # copy training set
            print("Copying Training Set")
            with tqdm(total=len(properties), unit=" dirs") as progressbar:
                for _, property_directory in property_directories:
                    progressbar.set_description(property_directory)
                    dst = os.path.join(
                        property_directory, GLOBALS.FILE_STRUCTURE["training_set"]
                    )
                    FileTools.copytree(GLOBALS.FILE_STRUCTURE["training_set"], dst)
                    progressbar.update()
            print()
            # copy sample pool
            print("Copying Sample Pool")
            with tqdm(total=len(properties), unit=" dirs") as progressbar:
                for _, property_directory in property_directories:
                    progressbar.set_description(property_directory)
                    dst = os.path.join(
                        property_directory, GLOBALS.FILE_STRUCTURE["sample_pool"]
                    )
                    FileTools.copytree(GLOBALS.FILE_STRUCTURE["sample_pool"], dst)
                    progressbar.update()
            print()
        else:
            for property_name in properties:
                property_directory = os.path.join(
                    properties_root, property_name
                )
                property_directories += [(property_name, property_directory)]
        # copy ICHOR.py
        print("Copying ICHOR")
        with tqdm(total=len(properties), unit=" files") as progressbar:
            for _, property_directory in property_directories:
                progressbar.set_description(property_directory)
                FileTools.copy_file(os.path.realpath(__file__), property_directory)
                progressbar.update()
        print()
        # copy config.properties
        print("Copying Config File")
        with tqdm(total=len(properties), unit=" files") as progressbar:
            for property_name, property_directory in property_directories:
                progressbar.set_description(property_directory)
                GLOBALS.OPTIMISE_PROPERTY = property_name
                with FileTools.pushd(property_directory):
                    GLOBALS.save_to_config()
                # FileTools.copy_file(Arguments.config_file, property_directory)
                progressbar.update()
        print()
        # copy programs
        print("Copying Programs")
        with tqdm(total=len(properties), unit=" files") as progressbar:
            for _, property_directory in property_directories:
                progressbar.set_description(property_directory)
                dst = os.path.join(
                    property_directory, GLOBALS.FILE_STRUCTURE["programs"]
                )
                FileTools.copytree(GLOBALS.FILE_STRUCTURE["programs"], dst)
                progressbar.update()
        print()
        # run adaptive sampling
        print("Submitting Adaptive Sampling Runs")
        importlib.invalidate_caches()
        for property_name, property_directory in property_directories:
            with FileTools.pushd(property_directory):
                spec = importlib.util.spec_from_file_location("*", __file__)
                ichor = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(ichor)
                except:
                    print(f"Error submitting adaptive sampling for: {property_name}")
                ichor.AutoTools.run_from_extern()

        GLOBALS.OPTIMISE_PROPERTY = original_property

    @staticmethod
    def collate_log():
        FileTools.mkdir(GLOBALS.FILE_STRUCTURE["log"], empty=False)
        for properties_dir in FileTools.get_files_in(
            GLOBALS.FILE_STRUCTURE["properties"], "*/"
        ):
            log_dir = os.path.join(properties_dir, GLOBALS.FILE_STRUCTURE["log"])
            if os.path.exists(log_dir):
                # for model_dir in FileTools.get_files_in(log_dir, f"{str(GLOBALS.SYSTEM_NAME)}*/"):
                FileTools.copymodels(log_dir, GLOBALS.FILE_STRUCTURE["log"])


# ========================#
#      Point Tools       #
# ========================#


def buildermethod(func):
    def wrapper(self, *args, **kwargs):
        func(self, *args, **kwargs)
        return self
    return wrapper


class Atom:
    ang2bohr = 1.88971616463
    counter = it.count(1)

    def __init__(self, coordinate_line):
        self.atom_type = ""
        self.atom_number = next(Atom.counter)

        self.x = 0
        self.y = 0
        self.z = 0

        self.read_input(coordinate_line)

        self._bonds = []
        self.__level = it.count(0)

        self.x_axis = None
        self.xy_plane = None

        self.features = []
        self.properties = None

    def read_input(self, coordinate_line):
        if isinstance(coordinate_line, str):
            find_atom = coordinate_line.split()
            self.atom_type = find_atom[0]
            coordinate_line = next(
                re.finditer(r"(\s*[+-]?\d+.\d+([Ee][+-]?\d+)?){3}", coordinate_line)
            ).group()
            coordinate_line = re.finditer(
                r"[+-]?\d+.\d+([Ee][+-]?\d+)?", coordinate_line
            )
            self.x = float(next(coordinate_line).group())
            self.y = float(next(coordinate_line).group())
            self.z = float(next(coordinate_line).group())
        elif isinstance(coordinate_line, Atom):
            self = coordinate_line
        elif isinstance(coordinate_line, (list, tuple)):
            if len(coordinate_line) == 3:
                self.atom_type = "H"
                self.x = float(coordinate_line[0])
                self.y = float(coordinate_line[1])
                self.z = float(coordinate_line[2])
            elif len(coordinate_line) == 4:
                self.atom_type = coordinate_line[0]
                self.x = float(coordinate_line[1])
                self.y = float(coordinate_line[2])
                self.z = float(coordinate_line[3])

    def sq_dist(self, other):
        return sum(
            (icoord - jcoord) ** 2
            for icoord, jcoord in zip(self.coordinates, other.coordinates)
        )

    def dist(self, other):
        return np.sqrt(self.sq_dist(other))

    def xdiff(self, other):
        return other.x - self.x

    def ydiff(self, other):
        return other.y - self.y

    def zdiff(self, other):
        return other.z - self.z

    def angle(self, atom1, atom2):
        temp = (
            self.xdiff(atom1) * self.xdiff(atom2)
            + self.ydiff(atom1) * self.ydiff(atom2)
            + self.zdiff(atom1) * self.zdiff(atom2)
        )
        return math.acos((temp / (self.dist(atom1) * self.dist(atom2))))

    def set_bond(self, jatom):
        if jatom not in self._bonds:
            self._bonds.append(jatom)

    def get_priorty(self, level):
        atoms = Atoms(self)
        for _ in range(level):
            atoms_to_add = []
            for atom in atoms:
                for bonded_atom in atom.bonds:
                    if bonded_atom not in atoms:
                        atoms_to_add.append(bonded_atom)
            atoms.add(atoms_to_add)
        return atoms.priority

    def reset_level(self):
        self.__level = it.count(0)

    def add_alf_atom(self, atom):
        if self.x_axis is None:
            self.x_axis = atom
        else:
            self.xy_plane = atom

    def C_1k(self):
        return [
            self.xdiff(self.x_axis) / self.dist(self.x_axis),
            self.ydiff(self.x_axis) / self.dist(self.x_axis),
            self.zdiff(self.x_axis) / self.dist(self.x_axis),
        ]

    def C_2k(self):
        xdiff1 = self.xdiff(self.x_axis)
        ydiff1 = self.ydiff(self.x_axis)
        zdiff1 = self.zdiff(self.x_axis)

        xdiff2 = self.xdiff(self.xy_plane)
        ydiff2 = self.ydiff(self.xy_plane)
        zdiff2 = self.zdiff(self.xy_plane)

        sigma_fflux = -(xdiff1 * xdiff2 + ydiff1 * ydiff2 + zdiff1 * zdiff2) / (
            xdiff1 * xdiff1 + ydiff1 * ydiff1 + zdiff1 * zdiff1
        )

        y_vec1 = sigma_fflux * xdiff1 + xdiff2
        y_vec2 = sigma_fflux * ydiff1 + ydiff2
        y_vec3 = sigma_fflux * zdiff1 + zdiff2

        yy = math.sqrt(y_vec1 * y_vec1 + y_vec2 * y_vec2 + y_vec3 * y_vec3)

        y_vec1 /= yy
        y_vec2 /= yy
        y_vec3 /= yy

        return [y_vec1, y_vec2, y_vec3]

    def C_3k(self, C_1k, C_2k):
        xx3 = C_1k[1] * C_2k[2] - C_1k[2] * C_2k[1]
        yy3 = C_1k[2] * C_2k[0] - C_1k[0] * C_2k[2]
        zz3 = C_1k[0] * C_2k[1] - C_1k[1] * C_2k[0]

        return [xx3, yy3, zz3]

    def calculate_features(self, atoms, unit="bohr"):
        ang2bohr = Atom.ang2bohr
        if "ang" in unit.lower():
            ang2bohr = 1.0

        x_bond = self.dist(self.x_axis)
        xy_bond = self.dist(self.xy_plane)
        angle = self.angle(self.x_axis, self.xy_plane)

        self.features += [x_bond * ang2bohr]
        self.features += [xy_bond * ang2bohr]
        self.features += [angle]

        for jatom in atoms:
            if jatom.num in self.alf_nums:
                continue
            self.features += [self.dist(jatom) * ang2bohr]

            C_1k = self.C_1k()
            C_2k = self.C_2k()
            C_3k = self.C_3k(C_1k, C_2k)

            xdiff = self.xdiff(jatom)
            ydiff = self.ydiff(jatom)
            zdiff = self.zdiff(jatom)

            zeta1 = C_1k[0] * xdiff + C_1k[1] * ydiff + C_1k[2] * zdiff
            zeta2 = C_2k[0] * xdiff + C_2k[1] * ydiff + C_2k[2] * zdiff
            zeta3 = C_3k[0] * xdiff + C_3k[1] * ydiff + C_3k[2] * zdiff

            # Calculate Theta
            self.features += [math.acos(zeta3 / self.dist(jatom))]

            # Calculate Phi
            self.features += [math.atan2(zeta2, zeta1)]

    def to_angstroms(self):
        self.x /= Atom.ang2bohr
        self.y /= Atom.ang2bohr
        self.z /= Atom.ang2bohr

    def to_bohr(self):
        self.x *= Atom.ang2bohr
        self.y *= Atom.ang2bohr
        self.z *= Atom.ang2bohr

    @property
    def priority(self):
        level = next(self.__level)
        return self.get_priorty(level)

    @property
    def bonds(self):
        return Atoms(self._bonds)

    @property
    def mass(self):
        return Constants.type2mass[self.atom_type]

    @property
    def radius(self):
        return Constants.type2rad[self.atom_type]

    @property
    def coordinates(self):
        return [self.x, self.y, self.z]

    @property
    def atom_num(self):
        return f"{self.atom_type}{self.atom_number}"

    @property
    def atom(self):
        return f"{self.atom_type}"

    @property
    def atom_num_coordinates(self):
        return [self.atom_num] + self.coordinates

    @property
    def atom_coordinates(self):
        return [self.atom] + self.coordinates

    @property
    def coordinates_string(self):
        width = str(16)
        precision = str(8)
        return f"{self.x:{width}.{precision}f}{self.y:{width}.{precision}f}{self.z:{width}.{precision}f}"

    @property
    def num(self):
        return self.atom_number

    @property
    def type(self):
        return self.atom_type

    @property
    def alf(self):
        alf = [self]
        if self.x_axis is not None:
            alf.append(self.x_axis)
        if self.xy_plane is not None:
            alf.append(self.xy_plane)
        return alf

    @property
    def alf_nums(self):
        return [atom.num for atom in self.alf]

    def __getattr__(self, attr):
        try:
            return self.__dict__[attr]
        except KeyError:
            return getattr(self.properties, attr)

    def __str__(self):
        return f"{self.atom_type:<3s}{self.coordinates_string}"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.atom_num == other.atom_num

    def __hash__(self):
        return hash(str(self.num) + str(self.coordinates_string))

    def __sub__(self, other):
        self.x -= other.x
        self.y -= other.y
        self.z -= other.z
        return self


class Atoms:
    ALF = []

    def __init__(self, atoms=None):
        self._atoms = []
        self._connectivity = None
        self._centred = False
        self.finish()

        if atoms is not None:
            self.add(atoms)

    def add(self, atom):
        if isinstance(atom, Atom):
            self._atoms.append(atom)
        elif isinstance(atom, str):
            self.add(Atom(atom))
        elif isinstance(atom, (list, Atoms)):
            for a in atom:
                self.add(a)

    def finish(self):
        Atom.counter = it.count(1)

    def connect(self, iatom, jatom):
        iatom.set_bond(jatom)
        jatom.set_bond(iatom)

    def to_angstroms(self):
        for atom in self:
            atom.to_angstroms()

    def to_bohr(self):
        for atom in self:
            atom.to_bohr()

    def calculate_alf(self):
        self.connectivity
        for iatom in self:
            for _ in range(2):
                queue = iatom.bonds - iatom.alf
                if queue.empty:
                    for atom in iatom.bonds:
                        queue.add(atom.bonds)
                    queue -= iatom.alf
                iatom.add_alf_atom(queue.max_priority)
        Atoms.ALF = self.alf
        self.set_alf()

    def set_alf(self):
        # self._atoms = sorted(self._atoms, key=lambda x: x.num)
        for atom, atom_alf in zip(self, Atoms.ALF):
            atom.x_axis = self[atom_alf[1] - 1]
            atom.xy_plane = self[atom_alf[2] - 1]

    def calculate_features(self):
        if not Atoms.ALF:
            self.calculate_alf()
        self.set_alf()
        for atom in self:
            atom.calculate_features(self)

    def centre(self, centre_atom=None):
        if isinstance(centre_atom, int):
            centre_atom = self[centre_atom]
        elif centre_atom is None:
            centre_atom = self.centroid

        for i, atom in enumerate(self):
            atom -= centre_atom

        self._centred = True

    def rotate(self, R):
        coordinates = R.dot(self.coordinates.T).T
        for atom, coordinate in zip(self, coordinates):
            atom.x = coordinate[0]
            atom.y = coordinate[1]
            atom.z = coordinate[2]

    def _rmsd(self, other):
        dist = 0
        for iatom, jatom in zip(self, other):
            dist += iatom.sq_dist(jatom)
        return np.sqrt(dist / len(self))

    def rmsd(self, other):
        if not self._centred:
            self.centre()
        if not other._centred:
            other.centre()

        P = self.coordinates
        Q = other.coordinates
        H = self.coordinates.T.dot(other.coordinates)

        V, S, W = np.linalg.svd(H)
        d = (np.linalg.det(V) * np.linalg.det(W)) < 0.0

        if d:
            S[-1] = -S[-1]
            V[:, -1] = -V[:, -1]

        R = np.dot(V, W)

        other.rotate(R)
        return self._rmsd(other)

    @property
    def coordinates(self):
        return np.array([atom.coordinates for atom in self])

    @property
    def centroid(self):
        coordinates = self.coordinates.T

        x = np.mean(coordinates[0])
        y = np.mean(coordinates[1])
        z = np.mean(coordinates[2])

        return Atom([x, y, z])

    @property
    def priority(self):
        return sum(self.masses)

    @property
    def max_priority(self):
        prev_priorities = []
        while True:
            priorities = [atom.priority for atom in self]
            if priorities.count(max(priorities)) == 1 or prev_priorities == priorities:
                break
            else:
                prev_priorities = priorities
        for atom in self:
            atom.reset_level()
        return self[priorities.index(max(priorities))]

    @property
    def masses(self):
        return [atom.mass for atom in self]

    @property
    def atoms(self):
        return [atom.atom_num for atom in self]

    @property
    def empty(self):
        return len(self) == 0

    @property
    @lru_cache()
    def connectivity(self):
        connectivity = np.zeros((len(self), len(self)))
        for i, iatom in enumerate(self):
            for j, jatom in enumerate(self):
                if iatom != jatom:
                    max_dist = 1.2 * (iatom.radius + jatom.radius)

                    if iatom.dist(jatom) < max_dist:
                        connectivity[i][j] = 1
                        self.connect(iatom, jatom)

        return connectivity

    @property
    def alf(self):
        return [[iatom.num for iatom in atom.alf] for atom in self]

    @property
    def features(self):
        try:
            return self._features
        except AttributeError:
            self.calculate_features()
            self._features = [atom.features for atom in self]
            return self._features

    @property
    def features_dict(self):
        try:
            return self._features_dict
        except AttributeError:
            self.calculate_features()
            self._features = {atom.atom_num: atom.features for atom in self}
            return self._features

    def __len__(self):
        return len(self._atoms)

    def __delitem__(self, i):
        del self._atoms[i]

    def __getitem__(self, i):
        return self._atoms[i]

    def __str__(self):
        return "\n".join([str(atom) for atom in self])

    def __repr__(self):
        return str(self)

    def __sub__(self, other):
        # other = sorted(Atoms(other), key=lambda x: x.num, reverse=False)
        for i, atom in enumerate(self):
            for jatom in other:
                if jatom == atom:
                    del self[i]
        return self

    def __bool__(self):
        return bool(self.atoms)


class PointError:
    class AtomsNotDefined(Exception):
        pass

    class AtomNotFound(Exception):
        pass

    class NotGJF(Exception):
        pass

    class NotGau(Exception):
        pass

    class NotWFN(Exception):
        pass

    class NotINT(Exception):
        pass

    class NotINTs(Exception):
        pass

    class CannotMove(Exception):
        pass


class Point:
    counter = it.count(1)

    @property
    def atoms(self):
        try:
            return self.gjf.atoms
        except:
            pass

        try:
            return self.wfn.atoms
        except:
            pass

        raise PointError.AtomsNotDefined()

    @property
    def features(self):
        return self.atoms.features

    @property
    def features_dict(self):
        return self.atoms.features_dict

    @property
    def iqa(self):
        return {_int.atom: _int.iqa for _int in self.ints}

    @property
    def natoms(self):
        return len(self.atoms)

    @property
    def dirname(self):
        return os.path.dirname(self.path)

    def exists(self):
        return os.path.exists(self.path)

    def move(self, dst):
        raise PointError.CannotMove()

    def get_property(self, property_names):
        properties = {}
        if not isinstance(property_names, list):
            property_names = [property_names]
        for atom, data in self.ints.items():
            for property_name in property_names:
                property_ = data.__getattr__(property_name)
                if not isinstance(property_, dict):
                    property_ = {property_name: property_}
                if atom not in properties.keys():
                    properties[atom] = {}
                properties[atom].update(property_)
        return properties

    def get_true_value(self, value_to_get, atoms=False):
        properties = self.get_property(value_to_get)
        values = [0] * len(self)
        for atom, data in properties.items():
            values[UsefulTools.get_number(atom) - 1] = data[value_to_get]

        return values if atoms else sum(values)

    def calculate_recovery_error(self):
        return np.abs(self.wfn.energy - self.get_true_value("iqa"))

    def get_integration_errors(self):
        return {atom: data.integration_error for atom, data in self.ints.items()}

    def __len__(self):
        return len(self.atoms)

    def __getitem__(self, i):
        return self.atoms[i]

    def __bool__(self):
        return self.path != ""


"""
class Point:
    counter = it.count(1)

    def __init__(
        self,
        directory="",
        gjf_fname="",
        wfn_fname="",
        int_directory="",
        int_fnames=[],
        read_gjf=False,
        read_wfn=False,
        read_ints=False,
        atoms=None,
    ):
        self.num = next(Point.counter)
        self.directory = directory
        self.gjf = GJF(gjf_fname, read=read_gjf)
        self.wfn = WFN(wfn_fname, read=read_wfn)
        self.int_directory = int_directory
        self.int_fnames = int_fnames
        self.ints = {}
        for int_fname in self.int_fnames:
            int_file = INT(int_fname, read=read_ints)
            self.ints[int_file.atom] = int_file

        self.fname = ""

        if atoms is not None:
            self.gjf._atoms = atoms

    @property
    def atoms(self):
        return self.gjf._atoms

    @property
    def features(self):
        return self.atoms.features

    @property
    def nfeats(self):
        return len(self.features)

    @property
    def natoms(self):
        return len(self.atoms)

    def find_wfn(self):
        wfns = FileTools.get_files_in(self.directory, "*.wfn")
        if len(wfns) > 0:
            self.wfn = WFN(wfns[0], read=True)

    def get_directory(self):
        return self.directory

    def get_true_value(self, value_to_get, atoms=False):
        if value_to_get == "iqa":
            eiqa = 0 if not atoms else [0] * len(self.atoms)
            for _, int_data in self.ints.items():
                if not atoms:
                    eiqa += int_data.eiqa
                else:
                    eiqa[int_data.num - 1] = int_data.eiqa
            return eiqa
        elif value_to_get == "q00":
            q00 = 0 if not atoms else [0] * len(self.atoms)
            for _, int_data in self.ints.items():
                if not atoms:
                    q00 += int_data.integration_results["q"]
                else:
                    q00[int_data.num - 1] = int_data.integration_results["q"]
            return q00
        elif value_to_get in Constants.multipole_names:
            mpole = 0 if not atoms else [0] * len(self.atoms)
            for _, int_data in self.ints.items():
                if not atoms:
                    mpole += int_data.multipoles[value_to_get]
                else:
                    mpole[int_data.num - 1] = int_data.multipoles[value_to_get]
            return mpole

    def calculate_recovery_error(self):
        wfn_energy = self.wfn.energy
        iqa_energy = self.get_true_value("iqa")
        return np.abs(wfn_energy - iqa_energy)

    def get_integration_errors(self):
        integration_errors = {}
        for atom, int_data in self.ints.items():
            integration_errors[atom] = int_data.integration_results["L"]
        return integration_errors

    def split_fname(self):
        self.dirname = os.path.dirname(self.fname)
        self.basename = os.path.basename(self.fname)

        self.extension = self.basename.split(".")[-1]
        self.point_name = self.basename.split(".")[0]

        try:
            self.point_num = re.findall(r"\d+$", self.point_name)[0]
            self.system_name = self.point_name.replace(self.point_num, "")
            self.point_num = int(self.point_num)
        except (IndexError, ValueError):
            self.point_num = 1
            self.system_name = GLOBALS.SYSTEM_NAME

    def __get_features(self):
        training_set = {}
        self.atoms.features
        for atom in self.atoms:
            training_set[atom.atom_num] = {"features": atom.features}
        return training_set

    def training_set_lines(self, model_type):
        model_types = {
            "iqa": self.iqa_training_set_line,
            "multipoles": self.multipole_training_set_line,
        }

        for multipole_name in Constants.multipole_names:
            model_types[multipole_name] = self.multipole_training_set_line

        delimiter = " "
        number_of_outputs = 25

        point_data = model_types[model_type]()
        point_lines = {}
        nproperties = 0
        for atom, data in point_data.items():
            features = delimiter.join(
                [str(feature) for feature in data["features"]]
            )
            nproperties = len(data["outputs"])
            outputs = UsefulTools.format_list(
                data["outputs"], number_of_outputs
            )
            outputs = delimiter.join([str(output) for output in outputs])
            point_lines[atom] = f"{features} {outputs}"

        return point_lines, nproperties

    def iqa_training_set_line(self):
        training_set = self.__get_features()
        for atom in training_set.keys():
            training_set[atom]["outputs"] = [self.ints[atom].eiqa]
        return training_set

    def multipole_training_set_line(self):
        training_set = self.__get_features()
        for atom in training_set.keys():
            training_set[atom]["outputs"] = [
                self.ints[atom].integration_results["q"]
            ] + list(self.ints[atom].multipoles.values())[1:25]
        return training_set

    def move(self, new_directory):
        FileTools.mkdir(new_directory)

        self.gjf.move(new_directory)
        self.wfn.move(new_directory)
        for int_file in self.int_fnames:
            int_file.move(new_directory)

        self.directory = new_directory
"""


class Directory(Point):
    def __init__(self, dirpath):
        self.path = dirpath

        self.gjf = None
        self.wfn = None
        self.ints = None

        self.gau = None

        self.parse()

    def parse(self):
        self.read_directory(self.path)

    def read_directory(self, path):
        file_extentsions = {
            ".gjf": self.add_gjf,
            ".wfn": self.add_wfn,
            ".int": self.add_int,
            ".gau": self.add_gau
        }
        with os.scandir(path) as it:
            for entry in it:
                if (
                    entry.is_file()
                    and FileTools.get_extension(entry) in file_extentsions.keys()
                ):
                    add = file_extentsions[FileTools.get_extension(entry)]
                    add(entry.path)
                elif entry.is_dir():
                    self.read_directory(entry.path)

    @buildermethod
    def read(self):
        self.read_all()

    @buildermethod
    def add_gjf(self, gjf):
        if isinstance(gjf, str):
            gjf = GJF(gjf)
        if not isinstance(gjf, GJF):
            raise PointError.NotGJF()
        self.gjf = gjf

    @buildermethod
    def add_wfn(self, wfn):
        if isinstance(wfn, str):
            wfn = WFN(wfn)
        if not isinstance(wfn, WFN):
            raise PointError.NotWFN()
        self.wfn = wfn

    @buildermethod
    def add_ints(self, intsdir):
        self.read_directory(intsdir)

    @buildermethod
    def add_int(self, int_):
        if self.ints is None:
            self.ints = INTs()
        self.ints.add(int_)

    @buildermethod
    def add_gau(self, gau):
        if isinstance(gau, str):
            gau = Gau(gau)
        if not isinstance(gau, Gau):
            raise PointError.NotGau()
        self.gau = gau

    @buildermethod
    def read_all(self):
        if self.gjf:
            self.read_gjf()
        if self.wfn:
            self.read_wfn()
        if self.ints:
            self.read_ints()

    @buildermethod
    def read_gjf(self):
        if self.gjf is None:
            self.read()
        try:
            self.gjf.read()
        except AttributeError:
            logger.warning(f"Cannot read GJF in {self.path}")

    @buildermethod
    def read_wfn(self):
        if self.wfn is None:
            self.read()
        try:
            self.wfn.read()
        except AttributeError:
            logger.warning(f"Cannot read WFN in {self.path}")

    @buildermethod
    def read_ints(self):
        self.ints.read(self.atoms if self.atoms else None)
        if self.atoms:
            for atom, int_ in zip(self, self.ints):
                atom.properties = int_

    @buildermethod
    def read_gau(self):
        self.gau.read()

    def move(self, dst):
        FileTools.mkdir(dst)

        if self.gjf:
            self.gjf.move(dst)
        if self.wfn:
            self.wfn.move(dst)
        if self.ints:
            self.ints.move(dst)

        self.path = dst

    def __bool__(self):
        return any(self.gjf, self.wfn, self.ints)

    def __eq__(self, other):
        return self.path == other.path


class GJF(Point):
    jobs = {"energy": "p", "opt": "opt", "freq": "freq"}

    def __init__(self, path=None):
        self.path = path
        self._atoms = Atoms()

        self.job_type = "energy"  # energy/opt/freq
        self.method = "b3lyp"
        self.basis_set = "6-31+g(d,p)"

        self.charge = 0
        self.multiplicity = 1

        self.header_line = ""

        self.title = FileTools.get_basename(self.path)
        self.wfn = WFN(self.path.replace(".gjf", ".wfn"))

        self.startup_options = []
        self.keywords = []

        super().__init__()

    @buildermethod
    def read(self):
        if not self:
            return
        with open(self.path, "r") as f:
            for line in f:
                if line.startswith("%"):
                    self.startup_options.append(line.strip().replace("%", ""))
                if line.startswith("#"):
                    keywords = line.split()
                    for keyword in keywords:
                        if "/" in keyword:
                            self.method = keyword.split("/")[0].upper()
                            self.basis_set = keyword.split("/")[1].lower()
                if re.match(r"^\s*\d+\s+\d+$", line):
                    self.charge = int(line.split()[0])
                    self.multiplicity = int(line.split()[1])
                if re.match(Patterns.COORDINATE_LINE, line):
                    self._atoms.add(line.strip())
                if line.endswith(".wfn"):
                    self._atoms.finish()
                    self.wfn.path = line.strip()

    @property
    def atoms(self):
        return self._atoms

    @property
    def job(self):
        return GJF.jobs[self.job_type]

    def format(self):
        if not self.atoms:
            self.read()

        if UsefulTools.in_sensitive(GLOBALS.METHOD, Constants.GAUSSIAN_METHODS):
            self.method = GLOBALS.METHOD
        else:
            print("Error: Unknown method {METHOD}")
            print("Check method in {GLOBALS.DEFAULT_CONFIG_FILE}")
            quit()

        self.basis_set = GLOBALS.BASIS_SET

        required_keywords = ["nosymm", "output=wfn"]
        self.keywords = list(set(self.keywords + GLOBALS.KEYWORDS + required_keywords))

        self.startup_options = [
            f"nproc={GLOBALS.GAUSSIAN_CORE_COUNT}",
            f"mem=1GB",
        ]

        self.header_line = f"#{self.job} {self.method}/{self.basis_set} {UsefulTools.unpack(self.keywords)}\n"

        self.wfn.path = self.path.replace(".gjf", ".wfn")

    def move(self, dst):
        if self:
            if dst.endswith(os.sep):
                dst = dst.rstrip(os.sep)

            name = os.path.basename(dst)
            new_name = os.path.join(dst, name + ".gjf")
            FileTools.move_file(self.path, new_name)
            self.path = new_name

    def write(self):
        self.format()
        with open(self.path, "w") as f:
            for startup_option in self.startup_options:
                f.write(f"%" + startup_option + "\n")
            f.write(f"{self.header_line}\n")
            f.write(f"{self.title}\n\n")
            f.write(f"{self.charge} {self.multiplicity}\n")
            for atom in self._atoms:
                f.write(f"{str(atom)}\n")
            f.write(f"\n{self.wfn.path}")

    def submit(self):
        SubmissionTools.make_g09_script(self, redo=True, submit=True)


class WFN(Point):
    def __init__(self, path=None):
        self.path = path
        self._atoms = Atoms()

        self.title = ""
        self.header = ""

        self.mol_orbitals = 0
        self.primitives = 0
        self.nuclei = 0
        self.method = "HF"

        self.energy = 0
        self.virial = 0

    @buildermethod
    def read(self, only_header=False):
        if not self:
            return
        if not os.path.exists(self.path):
            return
        with open(self.path, "r") as f:
            self.title = next(f)
            self.header = next(f)
            self.read_header()
            if only_header:
                return
            for line in f:
                if "CHARGE" in line:
                    self._atoms.add(line)
                if "CENTRE ASSIGNMENTS" in line:
                    self._atoms.finish()
                if "TOTAL ENERGY" in line:
                    self.energy = float(line.split()[3])
                    self.virial = float(line.split()[-1])

    def read_header(self):
        data = re.findall(r"\s\d+\s", self.header)

        self.mol_orbitals = int(data[0])
        self.primitives = int(data[1])
        self.nuclei = int(data[2])

        split_header = self.header.split()
        if split_header[-1] != "NUCLEI":
            self.method = split_header[-1]
        else:
            self.method = GLOBALS.METHOD

    @property
    def atoms(self):
        return self._atoms.to_angstroms()

    @property
    def aimall_complete(self):
        if not self.title:
            if self.exists():
                self.read()
            else:
                return False

        aim_directory = self.title.strip() + "_atomicfiles"
        aim_directory = os.path.join(self.dirname, aim_directory)

        if not os.path.exists(aim_directory):
            return False
        n_ints = sum(1 for f in os.listdir(aim_directory) if f.endswith(".int"))
        return n_ints == self.nuclei

    def move(self, dst):
        if self:
            if dst.endswith(os.sep):
                dst = dst.rstrip(os.sep)

            name = os.path.basename(dst)
            new_name = os.path.join(dst, name + ".wfn")
            FileTools.move_file(self.path, new_name)
            self.path = new_name

    def check_functional(self):
        if not self:
            return
        data = []
        with open(self.path, "r") as f:
            for i, line in enumerate(f):
                if i == 1:
                    if GLOBALS.METHOD.upper() not in line.upper():
                        f.seek(0)
                        data = f.readlines()
                    break

        if data != []:
            data[1] = data[1].strip() + "   " + str(GLOBALS.METHOD) + "\n"
            with open(self.path, "w") as f:
                f.writelines(data)


class INT(Point):
    def __init__(self, path, atom=None):
        self.path = path
        self.atom = os.path.splitext(os.path.basename(self.path))[0].upper()

        self.parent = atom

        self.integration_results = {}
        self.multipoles = {}
        self.iqa_data = {}

    @buildermethod
    def read(self):
        try:
            self.read_json()
        except json.decoder.JSONDecodeError:
            self.read_int()
            # Backup only if read correctly
            if self.integration_results:
                self.backup_int()
                self.write_json()

    @buildermethod
    def read_int(self):
        with open(self.path, "r") as f:
            for line in f:
                if "Results of the basin integration:" in line:
                    line = next(f)
                    while line.strip():
                        for match in re.finditer(Patterns.AIMALL_LINE, line):
                            tokens = match.group().split("=")
                            try:
                                self.integration_results[tokens[0].strip()] = float(
                                    tokens[-1]
                                )
                            except ValueError:
                                print(f"Cannot convert {tokens[-1]} to float")
                        line = next(f)
                if "Real Spherical Harmonic Moments Q[l,|m|,?]" in line:
                    line = next(f)
                    line = next(f)
                    line = next(f)
                    line = next(f)
                    while line.strip():
                        if "=" in line:
                            tokens = line.split("=")
                            try:
                                multipole = (
                                    tokens[0]
                                    .strip()
                                    .replace("[", "")
                                    .replace(",", "")
                                    .replace("]", "")
                                )
                                self.multipoles[multipole.lower()] = float(tokens[-1])
                            except ValueError:
                                print(f"Cannot convert {tokens[-1]} to float")
                        line = next(f)
                if 'IQA Energy Components (see "2EDM Note"):' in line:
                    line = next(f)
                    line = next(f)
                    while line.strip():
                        if "=" in line:
                            tokens = line.split("=")
                            try:
                                self.iqa_data[tokens[0].strip()] = float(tokens[-1])
                            except ValueError:
                                print(f"Cannot convert {tokens[-1]} to float")
                        line = next(f)
        if self.parent:
            self.rotate_multipoles()

    def rotate_multipoles(self):
        print(self.parent)
        quit()

    @buildermethod
    def read_json(self):
        with open(self.path, "r") as f:
            int_data = json.load(f)
            self.integration_results = int_data["integration"]
            self.multipoles = int_data["multipoles"]
            self.iqa_data = int_data["iqa_data"]

    def backup_int(self):
        FileTools.move_file(self.path, self.path + ".bak")

    def write_json(self):
        int_data = {
            "integration": self.integration_results,
            "multipoles": self.multipoles,
            "iqa_data": self.iqa_data,
        }

        with open(self.path, "w") as f:
            json.dump(int_data, f)

    @property
    def num(self):
        return int(re.findall("\d+", self.atom)[0])

    @property
    def integration_error(self):
        return self.integration_results["L"]

    @property
    def eiqa(self):
        return self.iqa_data["E_IQA(A)"]

    @property
    def iqa(self):
        return self.eiqa

    @property
    def q(self):
        return self.integration_results["q"]

    @property
    def dipole(self):
        return np.sqrt(sum([self.q10**2, self.q11c**2, self.q11s**2]))

    def get_property(self, property_name):
        return getattr(self, property_name)

    def move(self, dst):
        if self:
            if dst.endswith(os.sep):
                dst = dst.rstrip(os.sep)

            name = os.path.basename(dst)
            intdir = os.path.join(dst, name + "_atomicfiles")
            FileTools.mkdir(intdir)
            new_name = os.path.join(intdir, self.atom.lower() + ".int")

            FileTools.move_file(self.path, new_name)
            self.path = new_name

    def revert_backup(self):
        if os.path.exists(self.path + ".bak"):
            FileTools.move_file(self.path + ".bak", self.path)

    def __getattr__(self, attr):
        if attr in Constants.multipole_names:
            if attr == "q00":
                return self.q
            return self.multipoles[attr]
        else:
            if attr.lower() in ["iqa", "eiqa"]:
                return self.iqa
            elif attr.lower() in ["multipoles"]:
                return {
                    multipole_name: self.__getattr__(multipole_name)
                    for multipole_name in Constants.multipole_names
                }
            elif attr.lower() in ["all"]:
                return self.multipoles | {"iqa": self.iqa}
            return self.__dict__[attr]
    
    def __setattr__(self, attr, val):
        if attr in Constants.multipole_names:
            if attr == "q00":
                self.integration_results["q"] = val
            self.multipoles[attr] = val
        else:
            if attr.lower() in ["iqa", "eiqa"]:
                self.iqa_data["E_IQA(A)"] = val
            self.__dict__[attr] = val



class INTs(Point):
    def __init__(self):
        self.ints = []

    @buildermethod
    def add(self, int_):
        if isinstance(int_, str):
            int_ = INT(int_)
        if not isinstance(int_, INT):
            raise PointError.NotINT()
        self.ints += [int_]

    @buildermethod
    def read(self, parent_mol=None):
        for atom in zip(self):
            atom.read(parent[atom])
        self.sort()

    def sort(self):
        self.ints = UsefulTools.natural_sort_atom(self)

    def items(self):
        return [(_int.atom, _int) for _int in self]

    def get_atom(self, atom):
        for _int in self:
            if _int.atom == atom:
                return _int
        raise PointError.AtomNotFound()

    def move(self, dst):
        for _int in self:
            _int.move(dst)

    def dipole(self):
        return [i.dipole for i in self]

    def charge(self):
        return np.sqrt(sum(i.dipole**2 for i in self))

    def revert_backup(self):
        for i in self:
            i.revert_backup()

    def get(self, prop):
        return getattr(self, prop)

    def __getattr__(self, attr):
        if attr in self.__dict__.keys():
            return self.__dict__[attr]
        else:
            return {_int.atom: _int.__getattr__(attr) for _int in self}

    def __bool__(self):
        return bool(self.ints)

    def __getitem__(self, idx):
        if isinstance(idx, int):
            return self.ints[idx]
        elif isinstance(idx, str):
            return self.get_atom(idx)
        raise PointError.AtomNotFound()

    def __len__(self):
        return len(self.ints)


class Gau(Point):
    def __init__(self, path=None):
        self.path = path

        self.charge = None
        self.dipole = {}

    @buildermethod
    def read(self):
        with open(self.path, "r") as f:
            for line in f:
                if "Charge=" in line:
                    self.charge = float(line.split()[1])
                if "Dipole moment" in line:
                    line = next(f)
                    line_split = line.split()
                    self.dipole["x"] = float(line_split[1])
                    self.dipole["y"] = float(line_split[3])
                    self.dipole["z"] = float(line_split[5])
                    break


class Geometry(Point):
    def __init__(self, atoms):
        self._atoms = atoms

    @property
    def atoms(self):
        return self._atoms


@jit(nopython=True)
def numba_r_rbf(x_star, x, hp):
    n_train = x.shape[0]
    n_feat = x.shape[1]
    r = np.empty((n_train, 1))
    for i in np.arange(n_train):
        result = 0.0
        for j in np.arange(n_feat):
            xi = x_star[j]
            xj = x[i][j]
            xh = hp[j]
            if (j + 1) % 3 == 0:
                diff = np.abs(xi - xj)
                if diff > np.pi:
                    diff = diff - 2 * np.pi
                elif diff < -np.pi:
                    diff = 2 * np.pi + diff
                result += xh * diff * diff
            else:
                result += xh * (xi - xj) ** 2
        r[i] = np.exp(-result)
    return r


@jit(nopython=True)
def numba_R_rbf(x, hp):
    n_train = x.shape[0]
    n_feat = x.shape[1]
    R = np.empty((n_train, n_train))
    for i in np.arange(n_train):
        R[i][i] = 1
        for j in np.arange(i + 1, n_train):
            result = 0.0
            for k in np.arange(n_feat):
                xi = x[i][k]
                xj = x[j][k]
                xh = hp[k]
                if (k + 1) % 3 == 0:
                    diff = np.abs(xi - xj)
                    if diff > np.pi:
                        diff = diff - 2 * np.pi
                    elif diff < -np.pi:
                        diff = 2 * np.pi + diff
                    result += xh * diff * diff
                else:
                    result += xh * (xi - xj) ** 2
            result = np.exp(-result)
            R[i][j] = result
            R[j][i] = result
    return R


class Model:
    def __init__(self, fname, read_model=False):
        self.fname = fname

        self.directory = ""
        self.basename = ""

        self.system_name = ""
        self.type = ""
        self.atom_number = ""

        self.analyse_name()

        self.nTrain = 0
        self.nFeats = 0

        self.mu = 0
        self.sigma2 = 0

        self.normalise = False
        self.norm_min = []
        self.norm_max = []

        self.standardise = False
        self.stand_mu = []
        self.stand_var = []

        self.hyper_parameters = []
        self.weights = []

        self.y = []
        self.X = []
        if read_model and self.fname:
            self.read()
            if self.normalise:
                self.X = self.normalise_data(self.X)
            elif self.standardise:
                self.X = self.standardise_data(self.y)

    def normalise_data(self, data):
        for i in range(self.nFeats):
            self.norm_min.append(data[:, i].min(0))
            self.norm_max.append(data[:, i].max(0))
            data[:, i] = (data[:, i] - data[:, i].min(0)) / data[:, i].ptp(0)
        self.norm_min = np.array(self.norm_min)
        self.norm_max = np.array(self.norm_max)
        return data

    def normalise_array(self, array):
        return (array - self.norm_min) / (self.norm_max - self.norm_min)

    def standardise_data(self, data):
        for i in range(self.nFeats):
            self.stand_mu.append(data[:, i].mean(0))
            self.stand_var.append(data[:, i].std(0))
            data[:, i] = (data[:, i] - data[:, i].mean(0)) / data[:, i].std(0)
        self.stand_mu = np.array(self.stand_mu)
        self.stand_var = np.array(self.stand_var)
        return data

    def standardise_array(self, array):
        return (array - self.stand_mu) / self.stand_var

    @property
    def num(self):
        return int(self.atom_number)

    @property
    def i(self):
        return self.num - 1

    def read(self, up_to=None):
        if self.nTrain > 0:
            return
        with open(self.fname) as f:
            for line in f:
                if "norm" in line:
                    self.normalise = True
                if "stand" in line:
                    self.standardise = True
                if "Feature" in line:
                    self.nFeats = int(line.split()[1])
                if "Number_of_training_points" in line:
                    self.nTrain = int(line.split()[1])
                if "Mu" in line:
                    numbers = line.split()
                    self.mu = float(numbers[1])
                    self.sigma2 = float(numbers[3])
                if "Theta" in line:
                    line = next(f)
                    while ";" not in line:
                        self.hyper_parameters.append(float(line))
                        line = next(f)
                    self.hyper_parameters = np.array(self.hyper_parameters)
                if "Weights" in line:
                    line = next(f)
                    while ";" not in line:
                        self.weights.append(float(line))
                        line = next(f)
                    self.weights = np.array(self.weights)
                if "Property_value_Kriging_centers" in line:
                    line = next(f)
                    while "training_data" not in line:
                        self.y.append(float(line))
                        line = next(f)
                    self.y = np.array(self.y).reshape((-1, 1))
                if "training_data" in line:
                    line = next(f)
                    while ";" not in line:
                        self.X.append([float(num) for num in line.split()])
                        line = next(f)
                    self.X = np.array(self.X).reshape((self.nTrain, self.nFeats))

                if up_to is not None and up_to in line:
                    break

    def analyse_name(self):
        self.directory = os.path.dirname(self.fname)
        self.basename = os.path.basename(self.fname)

        fname_split = os.path.splitext(self.basename)[0].split("_")
        self.system_name = fname_split[0]
        self.type = fname_split[2].lower()
        self.atom_number = fname_split[3]

    def remove_no_noise(self):
        no_noise_line = -1
        data = []
        with open(self.fname, "r") as f:
            for i, line in enumerate(f):
                if "No_Noise" in line:
                    no_noise_line = i
                    f.seek(0)
                    data = f.readlines()
                    break
                if i > 10:
                    break
        if data and no_noise_line > 0:
            del data[no_noise_line]
            with open(self.fname, "w") as f:
                f.writelines(data)

    def get_fname(self, directory=None):
        if directory is None:
            directory = self.directory
        basename = f"{self.system_name}_kriging_{self.type}_{self.atom_number}.txt"
        return os.path.join(directory, basename)

    def copy_to_log(self):
        log_directory = GLOBALS.FILE_STRUCTURE["log"]
        FileTools.mkdir(log_directory)

        if self.nTrain == 0:
            self.read(up_to="Number_of_training_points")

        nTrain = str(self.nTrain).zfill(4)
        log_directory = os.path.join(log_directory, f"{self.system_name}{nTrain}")
        FileTools.mkdir(log_directory)
        log_model_file = self.get_fname(log_directory)

        FileTools.copy_file(self.fname, log_model_file)

    def r(self, features):
        return numba_r_rbf(features, self.X, np.array(self.hyper_parameters))

    @property
    def R(self):
        try:
            return self._R
        except AttributeError:
            self._R = numba_R_rbf(self.X, np.array(self.hyper_parameters))
            return self._R

    def add_nugget(self, nugget=1e-12):
        return self.R + np.eye(self.nTrain) * nugget

    @property
    def invR(self):
        try:
            return self._invR
        except AttributeError:
            try:
                self._invR = la.inv(self.R)
            except:
                nugget = float(GLOBALS.FEREBUS_NUGGET)
                oom = 0
                while nugget < float(GLOBALS.MAX_NUGGET):
                    nugget = GLOBALS.FEREBUS_NUGGET * 10 ** oom
                    R = self.add_nugget(nugget)
                    logger.warning(
                        f"Singular Matrix Encountered: Nugget of {nugget}  used on model {self.fname}:{self.nTrain}"
                    )
                    try:
                        self._invR = la.inv(R)
                        break
                    except la.LinAlgError:
                        if nugget <= float(GLOBALS.MAX_NUGGET):
                            logger.error(
                                f"Could not invert R Matrix of {self.fname}:{self.nTrain}: Singular Matrix Encountered"
                            )
                            sys.exit(1)
                        oom += 1
            return self._invR

    @property
    def ones(self):
        try:
            return self._ones
        except AttributeError:
            self._ones = np.ones((self.nTrain, 1))
            return self._ones

    @property
    def H(self):
        try:
            return self._H
        except AttributeError:
            self._H = np.matmul(
                self.ones,
                la.inv(np.matmul(self.ones.T, self.ones)).item() * self.ones.T,
            )
            return self._H

    @property
    def B(self):
        try:
            return self._B
        except AttributeError:
            self._B = np.matmul(
                (la.inv(np.matmul(np.matmul(self.ones.T, self.invR), self.ones))),
                np.matmul(np.matmul(self.ones.T, self.invR), self.y),
            ).item()
            return self._B

    @property
    def cross_validation(self):
        try:
            return self._cross_validation
        except AttributeError:
            d = self.y - self.B * self.ones

            self._cross_validation = []
            for i in range(self.nTrain):
                cve = (
                    np.matmul(
                        self.invR[i, :],
                        (d + (d[i] / self.H[i][i]) * self.H[:][i].reshape((-1, 1))),
                    )
                    / self.invR[i][i]
                )
                self._cross_validation.append(cve.item() ** 2)
            return self._cross_validation

    def predict(self, point):
        features = point.features[self.i]
        r = self.r(features)
        weights = self.weights.reshape((-1, 1))
        return self.mu + np.matmul(r.T, weights).item()

    def variance(self, point):
        r = self.r(point.features[self.i])

        res1 = np.matmul(r.T, np.matmul(self.invR, r))
        res2 = np.matmul(self.ones.T, np.matmul(self.invR, r))
        res3 = np.matmul(self.ones.T, np.matmul(self.invR, self.ones))

        return self.sigma2 * (1 - res1.item() + (1 + res2.item()) ** 2 / res3.item())

    def variance2(self, point):
        point = point.features[self.i]
        r = self.r(point)
        return 1 - np.matmul(r.T, np.matmul(self.invR, r))

    def distance_to_point(self, point):
        point = np.array(point.features[self.i]).reshape((1, -1))
        return distance.cdist(point, self.X)

    def closest_point(self, point):
        return self.distance_to_point(point).argmin()

    def cross_validation_error(self, point):
        return self.cross_validation[self.closest_point(point)]

    def link(self, dst_dir):
        abs_path = os.path.abspath(self.fname)
        dst = os.path.join(dst_dir, self.basename)
        if os.path.exists(dst):
            os.remove(dst)
        else:
            try:
                os.unlink(dst)
            except:
                pass
        os.symlink(abs_path, dst)


class Models:
    def __init__(self, directory, read_models=False):
        self._models = []
        self.directory = directory

        expected_improvement_functions = {
            "epe": self.expected_improvement_epe,
            "eped": self.expected_improvement_eped,
            "var": self.expected_improvement_var,
            "vard": self.expected_improvement_vard,
            "var2": self.expected_improvement_var2,
            "vard2": self.expected_improvement_vard2,
            "sigma": self.expected_improvement_var,
            "sigmu": self.expected_improvement_sigmu,
            "rand": self.expected_improvement_rand,
        }
        self.expected_improvement_function = expected_improvement_functions[
            str(GLOBALS.ADAPTIVE_SAMPLING_METHOD)
        ]

        if self.directory:
            self.find_models(read_models)

    def find_models(self, read_model=False):
        model_files = FileTools.get_files_in(self.directory, "*_kriging_*.txt")
        for model_file in tqdm(model_files):
            self.add(model_file, read_model)

    @property
    def nTrain(self):
        self[0].read(up_to="Theta")
        return self[0].nTrain

    def get(self, type):
        if type == "all":
            return [model for model in self]
        elif type == "multipoles":
            return [model for model in self if re.match(r"q\d+(\w+)?", model.type)]
        else:
            return [model for model in self if model.type == type]

    def read(self):
        for model in self:
            model.read()

    def read_first(self):
        self[0].read()

    def add(self, model_file, read_model=False):
        self._models.append(Model(model_file, read_model=read_model))

    @lru_cache()
    def predict(self, points, atoms=False, type="iqa", verbose=False):
        predictions = []
        models = self.get(type)
        with tqdm(
            total=len(points), unit=" points", leave=True, disable=not verbose
        ) as points_progressbar:
            for point in points:
                points_progressbar.set_description(point.path)
                prediction = 0 if not atoms else {}
                with tqdm(
                    total=len(models), unit=" models", leave=False, disable=not verbose,
                ) as models_progressbar:
                    for model in self.get(type):
                        models_progressbar.set_description(model.type)
                        if not atoms:
                            prediction += model.predict(point)
                        else:
                            if model.type not in prediction.keys():
                                prediction[model.type] = {}
                            prediction[model.type][model.num] = float(
                                model.predict(point)
                            )
                        models_progressbar.update()
                    predictions.append(prediction)
                points_progressbar.update()
        return np.array(predictions) if not atoms else predictions

    @lru_cache()
    def variance(self, points):
        variances = []
        for point in points:
            variance = sum(model.variance(point) for model in self)
            variances.append(variance)
        return np.array(variances)

    @lru_cache()
    def variance2(self, points):
        variances = []
        for point in points:
            variance = sum(model.variance2(point) for model in self)
            variances.append(variance)
        return np.array(variances).flatten()

    @lru_cache()
    def cross_validation(self, points):
        cross_validation_errors = []
        for point in points:
            cross_validation_error = sum(
                model.cross_validation_error(point) for model in self
            )
            cross_validation_errors.append(cross_validation_error)
        return np.array(cross_validation_errors)

    def distance_to_point(self, point, points):
        from scipy.spatial import distance

        distances = np.zeros(len(points))
        for atom in range(len(self)):
            point_features = np.array(point.features[atom]).reshape((1, -1))
            points_features = points.get_atom_features(atom)
            distances += distance.cdist(point_features, points_features).flatten() ** 2
        return np.sqrt(distances)

    def distances(self, points, added_points):
        distances = np.zeros(len(points))
        for added_point in added_points:
            distances += self.distance_to_point(added_point, points)
        return distances

    def calc_alpha(self):
        alpha_loc = GLOBALS.FILE_STRUCTURE["alpha"]
        if not os.path.exists(alpha_loc):
            return 0.5

        alpha = []
        with open(alpha_loc, "r") as f:
            data = json.load(f)
            if data["npoints"] != UsefulTools.nTrain():
                return 0.5
            for true_error, cv_error in zip(data["true_errors"], data["cv_errors"]):
                alpha.append(0.99 * min(0.5 * (float(true_error) / float(cv_error)), 1))

        if not alpha:
            return 0.5

        return np.mean(alpha)

    def calc_epe(self, points, added_points=[]):
        alpha = self.calc_alpha()

        logger.debug(f"Alpha: {alpha}")

        cv_errors = self.cross_validation(points)
        variances = self.variance(points)

        epe = alpha * cv_errors + (1 - alpha) * variances

        if added_points:
            added_points = [points[i] for i in added_points]
            _added_points = Set()
            [_added_points.add_dir(point) for point in added_points]
            distances = self.distances(points, _added_points)
            epe *= distances

        return epe

    def calc_var(self, points, added_points=[]):
        var = self.variance(points)

        if added_points:
            added_points = [points[i] for i in added_points]
            _added_points = Set()
            [_added_points.add_dir(point) for point in added_points]
            distances = self.distances(points, _added_points)
            var *= distances

        return var

    def calc_sigmu(self, points):
        sig = np.array(self.variance(points))
        mu = np.array([sum(model.predict(point) for model in self) for point in points])
        return sig * np.sqrt(np.abs(mu))

    def calc_var2(self, points, added_points=[]):
        var = self.variance2(points)

        if added_points:
            added_points = [points[i] for i in added_points]
            _added_points = Set()
            [_added_points.add_dir(point) for point in added_points]
            distances = self.distances(points, _added_points)
            var *= distances

        return var

    def write_data(self, indices, points):
        adaptive_sampling = GLOBALS.FILE_STRUCTURE["adaptive_sampling"]
        FileTools.mkdir(adaptive_sampling)

        cv_errors = self.cross_validation(points)
        predictions = self.predict(
            points, atoms=True, type=str(GLOBALS.OPTIMISE_PROPERTY)
        )

        data = {"npoints": UsefulTools.nTrain()}
        data["cv_errors"] = [float(cv_errors[index]) for index in indices]
        data["predictions"] = [predictions[index] for index in indices]
        with open(GLOBALS.FILE_STRUCTURE["cv_errors"], "w") as f:
            json.dump(data, f)

    def expected_improvement_epe(self, points):
        best_points = np.flip(np.argsort(self.calc_epe(points)), axis=-1)
        points_to_add = best_points[: min(len(points), GLOBALS.POINTS_PER_ITERATION)]
        self.write_data(points_to_add, points)
        return points_to_add

    def expected_improvement_eped(self, points):
        points_to_add = []
        for _ in range(GLOBALS.POINTS_PER_ITERATION):
            best_points = np.flip(
                np.argsort(self.calc_epe(points, added_points=points_to_add)), axis=-1,
            )
            points_to_add += [best_points[0]]
        self.write_data(points_to_add, points)
        return points_to_add

    def expected_improvement_var(self, points):
        best_points = np.flip(np.argsort(self.calc_var(points)), axis=-1)
        return best_points[: min(len(points), GLOBALS.POINTS_PER_ITERATION)]

    def expected_improvement_sigmu(self, points):
        best_points = np.flip(np.argsort(self.calc_sigmu(points)), axis=-1)
        return best_points[: min(len(points), GLOBALS.POINTS_PER_ITERATION)]

    def expected_improvement_vard(self, points):
        points_to_add = []
        for _ in range(GLOBALS.POINTS_PER_ITERATION):
            best_points = np.flip(
                np.argsort(self.calc_var(points, added_points=points_to_add)), axis=-1,
            )
            points_to_add += [best_points[0]]
        return points_to_add

    def expected_improvement_var2(self, points):
        best_points = np.flip(np.argsort(self.calc_var2(points)), axis=-1)
        return best_points[: min(len(points), GLOBALS.POINTS_PER_ITERATION)]

    def expected_improvement_vard2(self, points):
        points_to_add = []
        for _ in range(GLOBALS.POINTS_PER_ITERATION):
            best_points = np.flip(
                np.argsort(self.calc_var2(points, added_points=points_to_add)), axis=-1,
            )
            points_to_add += [best_points[0]]
        return points_to_add

    def expected_improvement_rand(self, points):
        return np.random.randint(low=0, high=len(points), size=int(GLOBALS.POINTS_PER_ITERATION))

    def expected_improvement(self, points):
        points_to_add = self.expected_improvement_function(points)
        return points.get(points_to_add)

    def __getitem__(self, i):
        return self._models[i]

    def __len__(self):
        return len(self._models)


class PointsError:
    class NotDirectory(Exception):
        pass


class Points:
    def log_warnings(self):
        if GLOBALS.WARN_RECOVERY_ERROR:
            n_recovery_error = 0
            for point in self:
                if point.wfn and point.ints:
                    recovery_error = point.calculate_recovery_error()
                    if recovery_error > GLOBALS.RECOVERY_ERROR_THRESHOLD:
                        logger.warning(
                            f"{point.path} | Recovery Error: {recovery_error * Constants.ha_to_kj_mol} kJ/mol"
                        )
                        n_recovery_error += 1
            if n_recovery_error > 0:
                logger.warning(
                    f"{n_recovery_error} points are above the recovery error threshold ({GLOBALS.RECOVERY_ERROR_THRESHOLD * Constants.ha_to_kj_mol} kJ/mol), consider removing these points or increasing precision"
                )

        if GLOBALS.WARN_INTEGRATION_ERROR:
            n_integration_error = 0
            for point in self:
                integration_errors = point.get_integration_errors()
                for atom, integration_error in integration_errors.items():
                    if integration_error > GLOBALS.INTEGRATION_ERROR_THRESHOLD:
                        logger.warning(
                            f"{point.path} | {atom} | Integration Error: {integration_error}"
                        )
                        n_integration_error += 1
            if n_integration_error > 0:
                logger.warning(
                    f"{n_integration_error} atoms are above the integration error threshold ({GLOBALS.INTEGRATION_ERROR_THRESHOLD}), consider removing these points or increasing precision"
                )

    @buildermethod
    def _from(self, points):
        for point in points:
            self.add(point)

    def add(self, point):
        self += point

    @staticmethod
    def reader(func):
        def wrapper(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            if GLOBALS.LOG_WARNINGS:
                self.log_warnings()
            return result

        return wrapper

    @staticmethod
    def revert_backup(ts_bak=False, sp_bak=False, vs_bak=False):
        if not any([ts_bak, sp_bak, vs_bak]):
            menu = Menu(title="Revert JSON Backup", auto_close=True)
            menu.add_option("1", "Training Set", Points.revert_backup, kwargs={"ts_bak": True})
            menu.add_option("2", "Sample Pool", Points.revert_backup, kwargs={"sp_bak": True})
            menu.add_option("3", "Validation Set", Points.revert_backup, kwargs={"vs_bak": True})
            menu.add_space()
            menu.add_option("a", "All of the Above", Points.revert_backup, kwargs={"ts_bak": True, "sp_bak": True, "vs_bak": True})
            menu.add_final_options()
            menu.run()


        if ts_bak:
            ts = Set(GLOBALS.FILE_STRUCTURE["training_set"])
            for training_point in ts:
                if training_point.ints:
                    training_point.ints.revert_backup()

        if sp_bak:
            sp = Set(GLOBALS.FILE_STRUCTURE["sample_pool"])
            for sample_point in sp:
                if sample_point.ints:
                    sample_point.ints.revert_backup()

        if vs_bak:
            vs = Set(GLOBALS.FILE_STRUCTURE["validation_set"])
            for validation_point in vs:
                if validation_point.ints:
                    validation_point.ints.revert_backup()


class Set(Points):
    def __init__(self, path=None):
        self.path = path
        self.points = []
        if self.path:
            self.parse()

    def parse(self):
        with os.scandir(self.path) as it:
            for entry in it:
                if entry.is_file() and FileTools.get_filetype(entry) in [
                    ".gjf",
                    ".wfn",
                    ".int",
                ]:
                    src = entry.path
                    dst = os.path.join(self.path, FileTools.get_basename(src))
                    FileTools.mkdir(dst, empty=False)
                    FileTools.move_file(src, dst)
                    self.add_dir(dst)
                elif entry.is_dir():
                    self.add_dir(entry.path)
        self.sort()

    @buildermethod
    @Points.reader
    def read(self):
        for point in self:
            point.read()

    @buildermethod
    def add_dir(self, _dir):
        if isinstance(_dir, str):
            _dir = Directory(_dir)
        if not isinstance(_dir, Directory):
            raise PointsError.NotDirectory()
        self += _dir

    @buildermethod
    @Points.reader
    def read_gjfs(self):
        for point in self:
            point.read_gjf()
            if not point.gjf:
                del self[point]

    @buildermethod
    @Points.reader
    def read_wfns(self):
        for point in self:
            point.read_wfn()

    @buildermethod
    @Points.reader
    def read_ints(self):
        for point in self:
            point.read_ints()

    @buildermethod
    def read_gau(self):
        for point in self:
            point.read_gau()

    @buildermethod
    def sort(self):
        self.points = UsefulTools.natural_sort_path(self)

    def n(self, attr):
        return sum(
            1
            for point in self
            if getattr(point, attr) is not None and getattr(point, attr).exists()
        )

    def check_functional(self):
        [point.wfn.check_functional() for point in self]

    def check_wfns(self):
        n_wfns = self.n("wfn")
        n_gjfs = self.n("gjf")
        if n_gjfs != n_wfns:
            wfns = Set(self.path)
            for point in self:
                if point.gjf and not point.wfn:
                    wfns.add(point)
            if n_gjfs > 0:
                print()
                print(f"{n_gjfs} GJFs found.")
                print(f"{n_wfns} WFNs found.")
                print()
                print(f"Submitting {n_gjfs - n_wfns} GJFs to Gaussian.")
                return wfns.submit_gjfs()
        else:
            if UsefulTools.in_sensitive(GLOBALS.METHOD, Constants.AIMALL_FUNCTIONALS):
                self.check_functional()
            print(f"{self.path}: All wfns complete.")

    def format_gjfs(self):
        for point in self:
            if point.gjf:
                point.gjf.write()

    def submit_gjfs(self, redo=False, submit=True, hold=None):
        return SubmissionTools.make_g09_script(
            self, redo=redo, submit=submit, hold=hold
        )

    def submit_wfns(self, redo=False, submit=True, hold=None, check_wfns=True):
        return SubmissionTools.make_aim_script(
            self, redo=redo, submit=submit, hold=hold, check_wfns=check_wfns
        )

    def make_training_set(self, model_type, npoints=-1):
        if npoints < 0:
            npoints = len(self)

        training_sets = {}
        for point in self:
            input = point.features_dict
            output = point.get_property(model_type)
            for atom in input.keys():
                if atom not in training_sets.keys():
                    training_sets[atom] = TrainingSet()

                training_sets[atom] += (input[atom], output[atom])

        for atom, training_set in training_sets.items():
            training_sets[atom] = training_set.slice(min(npoints, len(self)))

        # Write FEREBUS input files
        MAX_PROPERTIES = 25
        FileTools.mkdir(GLOBALS.FILE_STRUCTURE["ferebus"], empty=True)
        model_directories = []
        for atom, training_set in training_sets.items():
            directory = os.path.join(GLOBALS.FILE_STRUCTURE["ferebus"], atom)
            FileTools.mkdir(directory, empty=True)
            training_set_file = os.path.join(directory, atom + "_TRAINING_SET.txt")

            # Write Training Set File
            with open(training_set_file, "w") as f:
                for i, (input, output) in enumerate(training_set):
                    if len(output) > MAX_PROPERTIES:
                        output = dict(it.islice(output.items(), MAX_PROPERTIES))

                    num = f"{i+1}".zfill(4)
                    input = " ".join([str(s) for s in input])
                    output = " ".join([str(s) for s in output.values()])
                    f.write(f"{input} {output} {num}\n")

            # Write FINPUT.txt
            FerebusTools.write_finput(
                directory,
                len(training_sets),
                atom,
                len(training_set),
                nproperties=min(training_set.nproperties, MAX_PROPERTIES),
            )
            model_directories.append(directory)

        self.update_alpha()
        return model_directories

        # training_sets = {}

        # training_sets, nproperties = self.get_training_sets(model_type)

        # if model_type.lower() in Constants.multipole_names:
        #     nproperties = 1

        # FileTools.mkdir(GLOBALS.FILE_STRUCTURE["ferebus"], empty=True)
        # model_directories = []
        # for atom, training_set in training_sets.items():
        #     directory = os.path.join(GLOBALS.FILE_STRUCTURE["ferebus"], atom)
        #     FileTools.mkdir(directory, empty=True)
        #     training_set_file = os.path.join(
        #         directory, atom + "_TRAINING_SET.txt"
        #     )
        #     with open(training_set_file, "w") as f:
        #         for i, line in enumerate(training_set):
        #             num = f"{i+1}".zfill(4)
        #             f.write(f"{line} {num}\n")
        #     FerebusTools.write_finput(
        #         directory,
        #         len(training_sets.keys()),
        #         atom,
        #         len(training_set),
        #         model_type=model_type,
        #         nproperties=nproperties,
        #     )
        #     model_directories.append(directory)

        # self.update_alpha()

        # return model_directories

    def slice(self, *args):
        return Set()._from(it.islice(self, *args))

    def update_alpha(self):
        cv_file = GLOBALS.FILE_STRUCTURE["cv_errors"]
        if not os.path.exists(cv_file):
            return

        npoints = -1
        predictions = []
        cv_errors = []

        with open(cv_file, "r") as f:
            data = json.load(f)
            npoints = data["npoints"]
            cv_errors = data["cv_errors"]
            predictions = data["predictions"]

        true_values = []
        for point in self[npoints:]:
            true_values += [
                point.get_true_value(str(GLOBALS.OPTIMISE_PROPERTY), atoms=True)
            ]

        data = {}
        data["npoints"] = UsefulTools.nTrain()
        data["cv_errors"] = cv_errors
        data["true_errors"] = []
        for prediction, true_value in zip(predictions, true_values):
            true_error = sum(
                (true_value[int(predicted_atom) - 1] - predicted_value) ** 2
                for predicted_atom, predicted_value in prediction[
                    str(GLOBALS.OPTIMISE_PROPERTY)
                ].items()
            )

            data["true_errors"].append(true_error)

        FileTools.mkdir(GLOBALS.FILE_STRUCTURE["adaptive_sampling"])
        alpha_file = GLOBALS.FILE_STRUCTURE["alpha"]
        with open(alpha_file, "w") as f:
            json.dump(data, f)

    def __getitem__(self, idx):
        return self.points[idx]

    def __iadd__(self, other):
        if not isinstance(other, list):
            other = [other]
        self.points += other
        return self

    def __len__(self):
        return len(self.points)

    def __or__(self, other):
        for point in other:
            self.add(point)
            self.move(point)
        return self

    def __delitem__(self, idx):
        if isinstance(idx, (int, np.int64)):
            del self.points[idx]
        elif isinstance(idx, Directory):
            for i, point in enumerate(self):
                if point == idx:
                    del self.points[i]
                break

    def add(self, point):
        if isinstance(point, Directory):
            self += point
        elif isinstance(point, Atoms):
            self += Geometry(point)

    def get(self, points_to_get):
        points = Set()
        for point in reversed(sorted(points_to_get)):
            points.add(self[point])
            del self[point]
        return points

    def move(self, point):
        src = point.path

        idx = len(self)
        name = GLOBALS.SYSTEM_NAME + str(idx).zfill(4)
        dst = os.path.join(self.path, name)
        logger.info(f"Moving {src} -> {dst}")
        point.move(dst)

        FileTools.rmtree(src)


class MockDirectory(Directory):
    def __init__(self):
        self.path = ""

        self.gjf = GJF("")
        self.wfn = WFN("")
        self.ints = INTs()


class MockSet(Set):
    def __init__(self, npoints=0):
        self.points = [MockDirectory() for _ in range(npoints)]


class TrainingSet:
    def __init__(self):
        self.inputs = []
        self.outputs = []

    def to_list(self, l):
        return l if isinstance(l, list) else [l]

    def append(self, input, output):
        self.inputs.append(self.to_list(input))
        self.outputs.append(output)

    @buildermethod
    def _from(self, training_set):
        for training_point in training_set:
            self += training_point

    def slice(self, *args):
        return TrainingSet()._from(it.islice(self, *args))

    def __getitem__(self, idx):
        return (self.inputs[idx], self.outputs[idx])

    def __iadd__(self, other):
        self.append(other[0], other[1])
        return self

    def __repr__(self):
        repr = ""
        for input, output in self:
            input = " ".join([str(i) for i in input])
            output = str(output)
            repr += f"{input} | {output}\n"
        return repr

    @property
    def nproperties(self):
        return len(self.outputs[0])

    def __len__(self):
        return len(self.inputs)


"""
class Points:
    def __init__(
        self,
        directory="",
        read_gjfs=False,
        read_wfns=False,
        read_ints=False,
        first=False,
        read_directory=True,
    ):
        self._points = []

        self.directory = directory if directory else "."
        if read_gjfs or read_wfns or read_ints:
            FileTools.check_directory(self.directory)
            self.read_directory(
                read_gjfs,
                read_wfns=read_wfns,
                read_ints=read_ints,
                first=first,
            )
            if GLOBALS.LOG_WARNINGS:
                self.log_warnings()

        training_set_functions = {
            "min-max": self.get_min_max_features_first_atom,
            "random": self.get_random_points,
        }
        self._get_training_points = training_set_functions["min-max"]

    def read_point_directory(
        self, d, read_gjfs=False, read_wfns=False, read_ints=False, first=False
    ):
        point = {
            "read_gjf": read_gjfs,
            "read_wfn": read_wfns,
            "read_ints": read_ints,
            "directory": d,
        }

        for f in FileTools.get_files_in(d, "*", sort="natural"):
            if os.path.isdir(f):
                point["int_directory"] = f
                point["int_fnames"] = FileTools.get_files_in(
                    f, "*.int", sort="natural"
                )
            elif FileTools.get_filetype(f) == ".gjf":
                point["gjf_fname"] = f
            elif FileTools.get_filetype(f) == ".wfn":
                point["wfn_fname"] = f
        return point

    def read_directory(self, read_gjfs, read_wfns, read_ints, first=False):
        directories = FileTools.get_files_in(
            self.directory, "*/", sort="natural"
        )
        with tqdm(
            total=len(directories), unit=" files", leave=True
        ) as progressbar:
            for d in directories:
                progressbar.set_description(desc=d)
                point = self.read_point_directory(
                    d, read_gjfs, read_wfns, read_ints, first
                )  # implement multiprocessing
                progressbar.update()
                if "gjf_fname" in point.keys():
                    self.add_point(point)
                    if first:
                        break

    def read_set(self, files, stay=True):
        if isinstance(files, str):
            files = [files]
        with tqdm(total=len(files), unit=" files", leave=stay) as progressbar:
            for f in files:
                progressbar.set_description(desc=f)
                if os.path.isdir(f):
                    if "_atomicfiles" in f:
                        progressbar.update()
                        continue
                    self.read_set(
                        FileTools.get_files_in(f, "*", sort="natural"),
                        stay=False,
                    )
                elif f.endswith(".gjf"):
                    self.read_gjf(f)
                elif f.endswith(".xyz"):
                    self.read_xyz(f)
                elif f == "":
                    files += FileTools.get_files_in(f, "*", sort="natural")
                    continue
                progressbar.update()

    def log_warnings(self):
        if GLOBALS.WARN_RECOVERY_ERROR:
            n_recovery_error = 0
            for point in self:
                recovery_error = point.calculate_recovery_error()
                if recovery_error > GLOBALS.RECOVERY_ERROR_THRESHOLD:
                    logger.warning(
                        f"{point.path} | Recovery Error: {recovery_error} Ha"
                    )
                    n_recovery_error += 1
            if n_recovery_error > 0:
                logger.warning(
                    f"{n_recovery_error} points are above the recovery error threshold ({GLOBALS.RECOVERY_ERROR_THRESHOLD} Ha), consider removing these points or increasing precision"
                )

        if GLOBALS.WARN_INTEGRATION_ERROR:
            n_integration_error = 0
            for point in self:
                integration_errors = point.get_integration_errors()
                for atom, integration_error in integration_errors.items():
                    if integration_error > GLOBALS.INTEGRATION_ERROR_THRESHOLD:
                        logger.warning(
                            f"{point.path} | {atom} | Integration Error: {integration_error} Ha"
                        )
                        n_integration_error += 1
            if n_integration_error > 0:
                logger.warning(
                    f"{n_integration_error} atoms are above the integration error threshold ({GLOBALS.INTEGRATION_ERROR_THRESHOLD} Ha), consider removing these points or increasing precision"
                )

    def read_gjf(self, gjf_file):
        gjf = GJF(gjf_file, read=True)
        self.add_point(gjf._atoms)

    def read_xyz(self, xyz_file):
        trajectory = Trajectory(xyz_file, read=True)
        for point in trajectory:
            self.add_point(point)

    def add_point(self, point):
        if isinstance(point, dict):
            self._points.append(Point(**point))
        elif isinstance(point, Point):
            self._points.append(point)
        elif isinstance(point, Atoms):
            self._points.append(Point(atoms=point))

    def add(self, points, move=False):
        for point in points:
            self.add_point(point)
            if move:
                self.move(point)

    def move(self, point):
        old_directory = point.directory

        new_index = len(self) + 1
        subdirectory = GLOBALS.SYSTEM_NAME + str(new_index).zfill(4)
        new_directory = os.path.join(self.directory, subdirectory)
        point.move(new_directory)

        FileTools.rmtree(old_directory)

    def get_points(self, points_to_get):
        points = Points(self.directory)
        for point in reversed(sorted(points_to_get)):
            points.add_point(self[point])
            del self[point]
        return points

    def renumber(self):
        Point.counter = it.count(1)
        for point in self:
            point.num = next(Point.counter)

    def move_points(self, points):
        new_set = Points()
        for point in points:
            if isinstance(point, int):
                point = self[point]
            new_set.add_point(point)  # add point to new set
            del self[point]  # delete point from current set
            # append src indx -> dst indx
        new_set.renumber()  # numbers new set from 1, n
        return new_set  # returns set with new points added

    def write_to_directory(self, directory, empty=False):
        if os.path.isdir(directory) and not empty:
            print()
            print(f"{directory} exists.")
            empty = UsefulTools.check_bool(
                input(f"Would you like to empty {directory}? [Y/N]")
            )

        FileTools.mkdir(directory, empty=empty)
        for point in self:
            gjf_name = GLOBALS.SYSTEM_NAME + str(point.num).zfill(4) + ".gjf"
            gjf_name = os.path.join(directory, gjf_name)
            gjf = GJF(gjf_name)
            gjf._atoms = point.atoms
            gjf.write()
        FileTools.check_directory(directory)

    def get_atom_features(self, atom):
        return self.features[atom]

    def get_atom_feature(self, atom, feature):
        return [features[feature] for features in self.get_atom_features(atom)]

    def get_min_max_atom_feature(self, atom, feature):
        features = self.get_atom_feature(atom, feature)

        min_indx = int(np.argmin(features))
        max_indx = int(np.argmax(features))

        return min_indx, max_indx

    def get_min_max_of_atom(self, iatom):
        points = []
        for i in range(self.nfeats):
            imin, imax = self.get_min_max_atom_feature(iatom, i)
            points += [imin, imax]
        return points

    def get_min_max_features_first_atom(self):
        return self.get_min_max_of_atom(0)

    def get_random_points(self, n_points):
        return sorted(random.sample(self.range, n_points), reverse=True)

    def get_training_points(self):
        training_points = self._get_training_points()
        return self.move_points(training_points)

    def make_random_set(self, n_points):
        points = self.get_random_points(n_points)
        return self.move_points(points)

    def make_set(self, n_points, directory):
        # append directory to file
        if n_points < 0:
            points = self.get_training_points()
        else:
            points = self.make_random_set(n_points)
        points.write_to_directory(directory)

    def format_gjfs(self):
        for point in self:
            if point.gjf:
                point.gjf.write()

    def submit_gjfs(self, redo=False, submit=True, hold=None):
        return SubmissionTools.make_g09_script(
            self, redo=redo, submit=submit, hold=hold
        )

    def submit_wfns(self, redo=False, submit=True, hold=None):
        return SubmissionTools.make_aim_script(
            self, redo=redo, submit=submit, hold=hold
        )

    def submit_models(self, write_data=True):
        SubmissionTools.make_ferebus_script(self, write_data=write_data)

    def check_functional(self):
        for point in self:
            point.wfn.check_functional()

    def check_wfns(self):
        n_wfns = self.n_wfns
        n_gjfs = self.n_gjfs
        if n_gjfs != n_wfns:
            wfns = Points()
            for point in self:
                if point.gjf and not point.wfn:
                    wfns.add_point(point)
            if n_gjfs > 0:
                print()
                print(f"{n_gjfs} GJFs found.")
                print(f"{n_wfns} WFNs found.")
                print()
                print(f"Submitting {n_gjfs - n_wfns} GJFs to Gaussian.")
                wfns.submit_gjfs()
                sys.exit(0)
        else:
            if UsefulTools.in_sensitive(
                GLOBALS.METHOD, Constants.AIMALL_FUNCTIONALS
            ):
                self.check_functional()
            print("All wfns complete.")

    def make_gjf_template(self, n_points):
        for i in range(n_points):
            gjf_fname = os.path.join(
                self.directory,
                GLOBALS.SYSTEM_NAME + str(i + 1).zfill(4) + ".gjf",
            )
            self.add_point(Point(gjf_fname=gjf_fname))

    def make_wfn_template(self, n_points):
        for i in range(n_points):
            wfn_fname = os.path.join(
                self.directory,
                GLOBALS.SYSTEM_NAME + str(i + 1).zfill(4) + ".wfn",
            )
            self.add_point(Point(wfn_fname=wfn_fname))

    def get_training_sets(self, model_type):
        training_sets = {}
        nproperties = 0
        for point in self:
            point_data, nproperties = point.training_set_lines(model_type)
            for atom, line in point_data.items():
                if atom not in training_sets.keys():
                    training_sets[atom] = []
                training_sets[atom].append(line)
        return training_sets, nproperties

    def update_alpha(self):
        cv_file = GLOBALS.FILE_STRUCTURE["cv_errors"]
        if not os.path.exists(cv_file):
            return

        npoints = -1
        predictions = []
        cv_errors = []

        with open(cv_file, "r") as f:
            data = json.load(f)
            npoints = data["npoints"]
            cv_errors = data["cv_errors"]
            predictions = data["predictions"]

        true_values = []
        for point in self[npoints:]:
            true_values += [
                point.get_true_value(
                    str(GLOBALS.OPTIMISE_PROPERTY), atoms=True
                )
            ]

        data = {}
        data["npoints"] = UsefulTools.nTrain()
        data["cv_errors"] = cv_errors
        data["true_errors"] = []
        for prediction, true_value in zip(predictions, true_values):
            true_error = sum(
                (true_value[int(predicted_atom) - 1] - predicted_value) ** 2
                for predicted_atom, predicted_value in prediction[
                    str(GLOBALS.OPTIMISE_PROPERTY)
                ].items()
            )

            data["true_errors"].append(true_error)

        FileTools.mkdir(GLOBALS.FILE_STRUCTURE["adaptive_sampling"])
        alpha_file = GLOBALS.FILE_STRUCTURE["alpha"]
        with open(alpha_file, "w") as f:
            json.dump(data, f)

    def make_training_set(self, model_type):
        training_sets, nproperties = self.get_training_sets(model_type)

        if model_type.lower() in Constants.multipole_names:
            nproperties = 1

        FileTools.mkdir(GLOBALS.FILE_STRUCTURE["ferebus"], empty=True)
        model_directories = []
        for atom, training_set in training_sets.items():
            directory = os.path.join(GLOBALS.FILE_STRUCTURE["ferebus"], atom)
            FileTools.mkdir(directory, empty=True)
            training_set_file = os.path.join(
                directory, atom + "_TRAINING_SET.txt"
            )
            with open(training_set_file, "w") as f:
                for i, line in enumerate(training_set):
                    num = f"{i+1}".zfill(4)
                    f.write(f"{line} {num}\n")
            FerebusTools.write_finput(
                directory,
                len(training_sets.keys()),
                atom,
                len(training_set),
                model_type=model_type,
                nproperties=nproperties,
            )
            model_directories.append(directory)

        self.update_alpha()

        return model_directories

    def calculate_recovery_errors(self):
        import pandas as pd

        iqa_energies = {}
        wfn_energies = []
        for point in self:
            if point.wfn.energy != 0:
                wfn_energies += [point.wfn.energy]
            for int_atom, int_data in point.ints.items():
                if int_atom not in iqa_energies.keys():
                    iqa_energies[int_atom] = []
                iqa_energies[int_atom] += [int_data.eiqa]

        df = pd.DataFrame(iqa_energies)
        df.columns = UsefulTools.natural_sort(list(df.columns))
        df.loc[:, "Total"] = df.sum(axis=1)
        df["WFN"] = pd.to_numeric(wfn_energies, errors="coerce")

        df["error / Ha"] = (df["Total"] - df["WFN"]).abs()
        df["error / kJ/mol"] = df["error / Ha"] * Constants.ha_to_kj_mol
        df.to_csv("recovery_errors.csv")

        return df["error / kJ/mol"]

    @property
    def n_points(self):
        return len(self._points)

    @property
    def n_gjfs(self):
        n = 0
        for point in self:
            n = n + 1 if point.gjf else n
        return n

    @property
    def n_wfns(self):
        n = 0
        for point in self:
            n = n + 1 if point.wfn else n
        return n

    @property
    def nfeats(self):
        if len(self) > 0:
            return self[0].nfeats
        else:
            return 0

    @property
    def natoms(self):
        if len(self) > 0:
            return self[0].natoms
        else:
            return 0

    @property
    def range(self):
        return range(self.n_points)

    @property
    def features(self):
        #          iatom   ipoint   ifeat
        # features[natoms][npoints][nfeatures]
        try:
            return self._features
        except AttributeError:
            print("Calculating Features")
            self._features = [[] for _ in range(self.natoms)]
            with tqdm(total=self.n_points, unit=" molecules") as progressbar:
                for point in self:
                    for i, feature in enumerate(point.features):
                        self._features[i].append(feature)
                    progressbar.update()
            return self._features

    def __len__(self):
        num_points = FileTools.count_points_in(self.directory)
        if num_points == 0:
            return len(self._points)
        return num_points

    def __delitem__(self, del_point):
        if isinstance(del_point, (int, np.int64)):
            del self._points[del_point]
        elif isinstance(del_point, Point):
            for i, point in enumerate(self):
                if point.num == del_point.num:
                    del self[i]
                break

    def __getitem__(self, i):
        return self._points[i]
"""


class Trajectory:
    def __init__(self, fname, read=False):
        self.fname = fname
        self._trajectory = []

        if self.fname and read:
            self.read()

    def read(self):
        with open(self.fname, "r") as f:
            atoms = Atoms()
            for line in f:
                if not line.strip():
                    continue
                elif re.match(r"^\s+\d+$", line):
                    natoms = int(line)
                    while len(atoms) < natoms:
                        line = next(f)
                        if re.match(
                            r"\s*\w+(\s+[+-]?\d+.\d+([Ee]?[+-]?\d+)?){3}", line
                        ):
                            atoms.add(line)
                    atoms.finish()
                    self.add(atoms)
                    atoms = Atoms()

    def append(self, atoms):
        if isinstance(atoms, Atoms):
            self._trajectory.append(atoms)
        else:
            self._trajectory.append(Atoms(atoms))

    def add_point(self, atoms):
        self.append(atoms)

    def add(self, atoms):
        self.append(atoms)

    def extend(self, atoms):
        [self._trajectory.append(iatoms) for iatoms in atoms]

    def write(self, fname=None):
        if fname is None:
            fname = self.fname
        with open(fname, "w") as f:
            for i, atoms in enumerate(self):
                f.write(f"    {len(atoms)}\ni = {i}\n")
                f.write(f"{atoms}\n")

    def rmsd(self, ref=None):
        if ref is None:
            ref = self[0]
        elif isinstance(ref, int):
            ref = self[ref]

        rmsd = []
        for point in self:
            rmsd += [ref.rmsd(point)]
        return rmsd

    def to_dir(self, root, every=1):
        for i, geometry in enumerate(self):
            if i % every == 0:
                path = str(GLOBALS.SYSTEM_NAME) + str(i + 1).zfill(4) + ".gjf"
                gjf = GJF(os.path.join(root, path))
                gjf._atoms = geometry
                gjf.write()

    def __len__(self):
        return len(self._trajectory)

    def __getitem__(self, i):
        return self._trajectory[i]


class PointTools:
    @staticmethod
    def select_wfn():
        t = TabCompleter()
        t.setup_completer(t.path_completer)

        while True:
            ans = input("Enter WFN to Convert: ")
            if not os.path.exists(ans):
                print("Invalid Input")
                print(f"{ans} does not exist")
                print()
            elif not ans.endswith(".wfn"):
                print("Invalid Input")
                print(f"{ans} is not a .wfn file")
                print()
            else:
                return ans

    @staticmethod
    def select_gjf():
        t = TabCompleter()
        t.setup_completer(t.path_completer)

        ans = input("Enter GJF to Write To: ")
        if not ans.endswith(".gjf"):
            ans += ".gjf"
        return ans

    @staticmethod
    def wfn_to_gjf():
        wfn_file = PointTools.select_wfn()
        wfn = WFN(wfn_file, read=True)
        atoms = wfn._atoms
        atoms.to_angstroms()

        gjf_file = PointTools.select_gjf()
        gjf = GJF(gjf_file)
        gjf._atoms = atoms
        gjf.format()
        gjf.write()


#############################################
#               Miscellaneous               #
#############################################


class SSH:
    def __init__(self, machine):
        try:
            import paramiko
        except ImportError:
            print("Paramiko is reuired for ssh commands")
            print("Use 'pip install paramiko' to use ssh")
            sys.exit(0)

        self.username = ""
        self.password = ""

        self.machine = machine
        self.address = EXTERNAL_MACHINES[self.machine]

        self.ssh = paramiko.SSHClient()

        self.home_dir = ""

    @property
    def pwd(self):
        return self.execute("pwd")[1][0].strip()

    def connect(self):
        import paramiko

        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        while True:
            try:
                self.username = input("Username: ")
                self.password = getpass("Password: ")
                print()
                print("Connecting to server")
                self.ssh.connect(
                    self.address, username=self.username, password=self.password,
                )
                print("Connected to " + self.address)
                print()
                break
            except paramiko.ssh_exception.AuthenticationException:
                print("Username or Password is incorrect try again")
                print()

    def open(self):
        ncols, nrows = shutil.get_terminal_size(fallback=(80, 24))
        ncols = math.floor(ncols * 0.9)
        channel = self.ssh.invoke_shell(width=ncols, height=nrows)
        self.stdin = channel.makefile("wb")
        self.stdout = channel.makefile("r")
        self.pwd

    def execute(self, cmd):
        """

        :param cmd: the command to be executed on the remote computer
        :examples:  execute('ls')
                    execute('finger')
                    execute('cd folder_name')
        """
        cmd = cmd.strip("\n")
        self.stdin.write(cmd + "\n")
        finish = "end of stdOUT buffer. finished with exit status"
        echo_cmd = "echo {} $?".format(finish)
        self.stdin.write(echo_cmd + "\n")
        shin = self.stdin
        self.stdin.flush()

        shout = []
        sherr = []
        exit_status = 0
        for line in self.stdout:
            if str(line).startswith(cmd) or str(line).startswith(echo_cmd):
                # up for now filled with shell junk from stdin
                shout = []
            elif str(line).startswith(finish):
                # our finish command ends with the exit status
                exit_status = int(str(line).rsplit(maxsplit=1)[1])
                if exit_status:
                    # stderr is combined with stdout.
                    # thus, swap sherr with shout in a case of failure.
                    sherr = shout
                    shout = []
                break
            else:
                shout.append(line)
                # get rid of 'coloring and formatting' special characters
                # shout.append(re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]').sub('', line).
                #              replace('\b', '').replace('\r', ''))
                pass

        # first and last lines of shout/sherr contain a prompt
        if shout and echo_cmd in shout[-1]:
            shout.pop()
        if shout and cmd in shout[0]:
            shout.pop(0)
        if sherr and echo_cmd in sherr[-1]:
            sherr.pop()
        if sherr and cmd in sherr[0]:
            sherr.pop(0)

        if len(shout) > 0:
            print("".join(shout))

        return shin, shout, sherr

    def close(self):
        del self

    def __del__(self):
        self.ssh.close()


class DlpolyTools:
    model_loc = "all"
    use_every = 1

    @staticmethod
    def write_control(control_file):
        with open(control_file, "w+") as f:
            f.write(f"Title: {GLOBALS.SYSTEM_NAME}\n")
            f.write(
                "# This is a generic CONTROL file. Please adjust to your requirement.\n"
            )
            f.write("# Directives which are commented are some useful options.\n\n")
            f.write("ensemble nvt hoover 0.02\n")
            if int(GLOBALS.DLPOLY_TEMPERATURE) == 0:
                f.write("temperature 10.0\n\n")
                f.write("#perform zero temperature run (really set to 10K)\n")
                f.write("zero\n")
            else:
                f.write(f"temperature {GLOBALS.DLPOLY_TEMPERATURE}\n\n")
            f.write("# Cap forces during equilibration, in unit kT/angstrom.\n")
            f.write("# (useful if your system is far from equilibrium)\n")
            f.write("cap 100.0\n\n")
            f.write("no vdw\n\n")
            f.write(f"steps {GLOBALS.DLPOLY_NUMBER_OF_STEPS}\n")
            f.write(f"equilibration {GLOBALS.DLPOLY_NUMBER_OF_STEPS}\n")
            f.write(f"timestep {GLOBALS.DLPOLY_TIMESTEP}\n")
            f.write("cutoff 15.0\n")
            f.write("fflux\n\n")
            if GLOBALS.DLPOLY_TEMPERATURE == 0 and GLOBALS.DLPOLY_CHECK_CONVERGENCE:
                f.write("converge\n")
                if GLOBALS.DLPOLY_CONVERGENCE_CRITERIA > 0:
                    f.write(f"criteria {GLOBALS.DLPOLY_CONVERGENCE_CRITERIA}\n")
                if GLOBALS.DLPOLY_MAX_ENERGY > 0:
                    f.write(f"max_energy {GLOBALS.DLPOLY_MAX_ENERGY}\n")
                if GLOBALS.DLPOLY_MAX_FORCE > 0:
                    f.write(f"max_force {GLOBALS.DLPOLY_MAX_FORCE}\n")
                if GLOBALS.DLPOLY_RMS_FORCE > 0:
                    f.write(f"rms_force {GLOBALS.DLPOLY_RMS_FORCE}\n")
                if GLOBALS.DLPOLY_MAX_DISP > 0:
                    f.write(f"max_disp {GLOBALS.DLPOLY_MAX_DISP}\n")
                if GLOBALS.DLPOLY_RMS_DISP > 0:
                    f.write(f"rms_disp {GLOBALS.DLPOLY_RMS_DISP}\n")
            if GLOBALS.KERNEL.lower() != "rbf":
                f.write(f"fflux_kernel {GLOBALS.KERNEL}")
            f.write("# Continue MD simulation\n")
            f.write("traj 0 1 2\n")
            f.write(f"print every {GLOBALS.DLPOLY_PRINT_EVERY}\n")
            f.write(f"stats every {GLOBALS.DLPOLY_PRINT_EVERY}\n")
            f.write("job time 10000000\n")
            f.write("close time 20000\n")
            f.write("finish")

    @staticmethod
    def write_config(config_file, atoms):
        with open(config_file, "w+") as f:
            f.write("DL_POLY CONFIG file converted using ICHOR\n")
            f.write("\t0\t0\n")
            for atom in atoms:
                f.write(f"{atom.type} {atom.num}\n")
                f.write(f"{atom.x}\t\t{atom.y}\t\t{atom.z}\n")

    @staticmethod
    def write_field(field_file, atoms):
        with open(field_file, "w") as f:
            f.write("DL_FIELD v3.00\nUnits internal\nMolecular types 1\n")
            f.write(f"Molecule name {GLOBALS.SYSTEM_NAME}\n")
            f.write("nummols 1\n")
            f.write(f"atoms {len(atoms)}\n")
            for atom in atoms:
                f.write(
                    f"{atom.type}\t\t{Constants.dlpoly_weights[atom.type]:.7f}     0.0   1   0\n"
                )
            f.write("finish\nclose")

    @staticmethod
    def write_kriging(kriging_file, atoms, models):
        atoms.calculate_alf()
        models.read()

        with open(kriging_file, "w+") as f:
            f.write(
                f"{GLOBALS.SYSTEM_NAME}\t\t#prefix of model file names for the considered system\n"
            )
            f.write(f"{len(atoms)}\t\t#number of atoms in the kriged system\n")
            f.write(
                "3\t\t#number of moments (first 3 are to be IQA energy components xc slf src)\n"
            )
            f.write(f"{models.nTrain}\t\t#max number of training examples\n")
            for i, atom in enumerate(atoms):
                f.write(f"{atom.type} {atom.num} {atom.x_axis.num} {atom.xy_plane.num}")
                for j in range(len(atoms)):
                    f.write(" 0") if i == j else f.write(f" {j+1}")
                f.write("\n")

    @staticmethod
    def link_models(model_dir, models):
        FileTools.mkdir(model_dir)
        for model in models:
            model.link(model_dir)

    @staticmethod
    def setup_dlpoly_dir(dlpoly_dir, models):
        FileTools.mkdir(dlpoly_dir)

        control_file = os.path.join(dlpoly_dir, "CONTROL")
        config_file = os.path.join(dlpoly_dir, "CONFIG")
        field_file = os.path.join(dlpoly_dir, "FIELD")
        kriging_file = os.path.join(dlpoly_dir, "KRIGING.txt")
        dlpoly_model_dir = os.path.join(dlpoly_dir, "model_krig")

        sp_dir = GLOBALS.FILE_STRUCTURE["sample_pool"]

        atoms = GJF(FileTools.get_first_gjf(sp_dir)).read().atoms

        DlpolyTools.write_control(control_file)
        DlpolyTools.write_config(config_file, atoms)
        DlpolyTools.write_field(field_file, atoms)
        DlpolyTools.write_kriging(kriging_file, atoms, models)
        DlpolyTools.link_models(dlpoly_model_dir, models)

    @staticmethod
    def setup_model(model_directory=None):
        dlpoly_dir = GLOBALS.FILE_STRUCTURE["dlpoly"]
        models = Models(model_directory)

        model_dir_name = FileTools.end_of_path(model_directory)
        dlpoly_model_dir = os.path.join(dlpoly_dir, model_dir_name)
        DlpolyTools.setup_dlpoly_dir(dlpoly_model_dir, models)

        return dlpoly_model_dir

    @staticmethod
    def run_on_model():
        model_dir = GLOBALS.FILE_STRUCTURE["models"]

        dlpoly_directories = [DlpolyTools.setup_model(model_dir)]
        SubmissionTools.make_dlpoly_script(dlpoly_directories, submit=True)

    @staticmethod
    def run_on_log():
        log_dir = GLOBALS.FILE_STRUCTURE["log"]

        model_dirs = FileTools.get_files_in(log_dir, GLOBALS.SYSTEM_NAME + "*/")
        dlpoly_directories = []
        for model_dir in model_dirs:
            dlpoly_directory = DlpolyTools.setup_model(model_dir)
            dlpoly_directories += [dlpoly_directory]

        return SubmissionTools.make_dlpoly_script(dlpoly_directories, submit=True)

    # TODO - fix for auto analysis single point
    @staticmethod
    @UsefulTools.external_function()
    def calculate_gaussian_energies():
        dlpoly_dir = GLOBALS.FILE_STRUCTURE["dlpoly"]
        trajectory_files = {}
        for model_dir in FileTools.get_files_in(dlpoly_dir, "*/"):
            trajectory_file = os.path.join(model_dir, "TRAJECTORY.xyz")
            if os.path.exists(trajectory_file):
                model_name = FileTools.end_of_path(model_dir)
                trajectory_files[model_name] = Trajectory(trajectory_file, read=True)

        for model_name, trajectory in trajectory_files.items():
            if len(trajectory) > 0:
                gjf_fname = os.path.join(dlpoly_dir, model_name, model_name + ".gjf")
                gjf = GJF(gjf_fname)
                gjf._atoms = trajectory[-1]
                gjf.write()

        submit_gjfs(dlpoly_dir)

    @staticmethod
    @UsefulTools.external_function()
    def get_wfn_energies():
        dlpoly_dir = GLOBALS.FILE_STRUCTURE["dlpoly"]
        points = Set(dlpoly_dir).read_wfns()
        energy_file = os.path.join(dlpoly_dir, "Energies.txt")
        with open(energy_file, "w") as f:
            for point in points:
                if point.wfn and re.findall(r"\d+", point.wfn.path):
                    point_num = int(re.findall(r"\d+", point.wfn.path)[-1])
                    f.write(f"{point.wfn.path} {point_num:4d} {point.wfn.energy}\n")
                    print(point.wfn.path, point_num, point.wfn.energy)

    @staticmethod
    def auto_run():
        FileTools.rmtree(GLOBALS.FILE_STRUCTURE["dlpoly"])

        log_dir = GLOBALS.FILE_STRUCTURE["log"]
        npoints = FileTools.count_models(log_dir)

        _, jid = DlpolyTools.run_on_log()
        _, jid = AutoTools.submit_dlpoly_gjfs(jid)
        _, jid = AutoTools.submit_gjfs(jid, npoints=npoints)
        AutoTools.submit_dlpoly_energies(jid)

    @staticmethod
    def calculate_trajectory_wfn(trajectory_file, d=None):
        if os.path.isdir(trajectory_file):
            trajectory_file = os.path.join(trajectory_file, "TRAJECTORY.xyz")

        trajectory_dir = os.path.dirname(trajectory_file)
        trajectory_gjf_dir = os.path.join(trajectory_dir, "TRAJECTORY")
        FileTools.mkdir(trajectory_gjf_dir, empty=True)

        trajectory = Trajectory(trajectory_file, read=True)
        for i, timestep in enumerate(trajectory):
            if i % DlpolyTools.use_every == 0:
                gjf_fname = GLOBALS.SYSTEM_NAME + str(i + 1).zfill(4) + ".gjf"
                gjf_fname = os.path.join(trajectory_gjf_dir, gjf_fname)

                gjf = GJF(gjf_fname)
                gjf._atoms = timestep
                gjf.write()

        if d is not None:
            modify = "trajectory"
            modify += "_" + str(d)
        return submit_gjfs(trajectory_gjf_dir)

    @staticmethod
    def calculate_trajectories_wfn():
        dlpoly_dir = GLOBALS.FILE_STRUCTURE["dlpoly"]
        jid = None
        for model_dir in FileTools.get_files_in(dlpoly_dir, "*/"):
            trajectory_file = os.path.join(model_dir, "TRAJECTORY.xyz")
            if os.path.exists(trajectory_file):
                model_name = FileTools.end_of_path(model_dir)
                _, jid = DlpolyTools.calculate_trajectory_wfn(
                    trajectory_file, d=model_name
                )
        return jid

    @staticmethod
    @UsefulTools.external_function()
    def get_trajectory_energies():
        import pandas as pd

        dlpoly_dir = GLOBALS.FILE_STRUCTURE["dlpoly"]

        trajectories = {}
        for model_dir in FileTools.get_files_in(dlpoly_dir, "*/"):
            trajectory_dir = os.path.join(model_dir, "TRAJECTORY/")
            if os.path.exists(trajectory_dir):
                model_name = FileTools.end_of_path(model_dir)
                trajectories[model_name] = DlpolyTools.get_trajectory_energy(
                    trajectory_dir
                )

        maxlen = max(len(energies) for _, energies in trajectories.items())
        for key, energies in trajectories.items():
            trajectories[key] = energies + [np.NaN] * (maxlen - len(energies))

        df = pd.DataFrame(trajectories)
        df.to_csv("TRAJECTORY.csv")

    # TODO - fix auto run
    @staticmethod
    def auto_traj_analysis():
        if DlpolyTools.model_loc == "all":
            jid = DlpolyTools.calculate_trajectories_wfn()
            AutoTools.submit_dlpoly_trajectories_energies(jid)
        else:
            jid = DlpolyTools.calculate_trajectory_wfn(DlpolyTools.model_loc)
            AutoTools.submit_dlpoly_trajectory_energies(
                jid, directory=DlpolyTools.model_loc
            )

    @staticmethod
    def get_dir():
        t = TabCompleter()
        t.setup_completer(t.path_completer)

        ans = input("Enter Directory Containing Trajectoy: ")
        if not os.path.isdir(ans):
            print("Invalid Input")
            print(f"{ans} is not a directory")
            print()
        elif not os.path.exists(os.path.join(ans, "TRAJECTORY.xyz")):
            print("Invalid Input")
            print(f"{ans} does not contain a TRAJECTORY.xyz file")
            print()
        else:
            return ans

    @staticmethod
    def _set_model(model=None):
        if not model:
            model = DlpolyTools.get_dir()
        DlpolyTools.model_loc = model

    @staticmethod
    def choose_model():
        model_menu = Menu(title="Select Model Directory", auto_close=True)

        dlpoly_dir = GLOBALS.FILE_STRUCTURE["dlpoly"]
        model_dirs = FileTools.get_files_in(dlpoly_dir, "*/")
        i = 1
        for model_dir in model_dirs:
            if os.path.exists(os.path.join(model_dir, "TRAJECTORY.xyz")):
                model_menu.add_option(
                    str(i),
                    model_dir,
                    DlpolyTools._set_model,
                    kwargs={"model": model_dir},
                )
                i += 1
        model_menu.add_space()
        model_menu.add_option(
            "a",
            "Use All Model Directories",
            DlpolyTools._set_model,
            kwargs={"model": "all"},
        )
        model_menu.add_option("c", "Custom Directory", DlpolyTools._set_model)
        model_menu.add_final_options(exit=False)
        model_menu.run()

    @staticmethod
    def change_every():
        every = 0
        print("Select Value To Use Every nth Point In Trajectory")
        while True:
            every = input("Enter Value: ")
            try:
                every = int(every)
                if every > 0:
                    break
                else:
                    print("Error: Value must be a positive integer")
                    print()
            except:
                print(f"Error: Cannot convert {every} to Integer")
                print()
        DlpolyTools.use_every = every

    @staticmethod
    def get_trajectory_directories():
        if DlpolyTools.model_loc == "all":
            dlpoly_dir = GLOBALS.FILE_STRUCTURE["dlpoly"]
            return FileTools.get_files_in(dlpoly_dir, "*/")
        else:
            return [DlpolyTools.model_loc]

    @staticmethod
    def submit_trajectory_to_gaussian():
        directories = DlpolyTools.get_trajectory_directories()
        for directory in directories:
            traj_file = os.path.join(directory, "TRAJECTORY.xyz")
            if os.path.isfile(traj_file):
                directory = os.path.join(directory, "TRAJECTORY")
                FileTools.mkdir(directory)
                trajectory = Trajectory(traj_file, read=True)
                trajectory.to_dir(directory, DlpolyTools.use_every)
                submit_gjfs(directory)

    @staticmethod
    def submit_trajectory_to_aimall():
        directories = DlpolyTools.get_trajectory_directories()
        for directory in directories:
            traj_dir = os.path.join(directory, "TRAJECTORY")
            if os.path.isdir(traj_dir):
                submit_wfns(traj_dir)

    @staticmethod
    def auto_run_trajectory_analysis():
        directories = DlpolyTools.get_trajectory_directories()
        for directory in directories:
            traj_file = os.path.join(directory, "TRAJECTORY.xyz")
            if os.path.isfile(traj_file):
                directory = os.path.join(directory, "TRAJECTORY")
                FileTools.mkdir(directory)
                trajectory = Trajectory(traj_file, read=True)
                trajectory.to_dir(directory, DlpolyTools.use_every)
                AutoTools.submit_aimall(directory)
        # Look at adding analysis at the end
        # maybe write to directory and run process after each
        # job finishes to check whether to run analysis

    @staticmethod
    @UsefulTools.external_function()
    def get_trajectory_energy(trajectory_dir):
        if FileTools.end_of_path(trajectory_dir) != "TRAJECTORY":
            trajectory_dir = os.path.join(trajectory_dir, "TRAJECTORY")
        points = Set(trajectory_dir).read_wfns()
        return [point.wfn.energy for point in points if point.wfn]

    @staticmethod
    def get_trajectory_gaussian_energies():
        import pandas as pd

        directories = DlpolyTools.get_trajectory_directories()
        trajectories = {}
        for directory in directories:
            traj_dir = os.path.join(directory, "TRAJECTORY")
            model_name = FileTools.end_of_path(directory)
            trajectories[model_name] = DlpolyTools.get_trajectory_energy(traj_dir)

            maxlen = max(len(energies) for _, energies in trajectories.items())
            for key, energies in trajectories.items():
                trajectories[key] = energies + [np.NaN] * (maxlen - len(energies))

        df = pd.DataFrame(trajectories)

        dlpoly_dir = GLOBALS.FILE_STRUCTURE["dlpoly"]
        df.to_excel(os.path.join(dlpoly_dir, "TRAJECTORY_Energies.xlsx"))

    @staticmethod
    @UsefulTools.external_function()
    def get_trajectory_aimall_energy(trajectory_dir):
        if FileTools.end_of_path(trajectory_dir) != "TRAJECTORY":
            trajectory_dir = os.path.join(trajectory_dir, "TRAJECTORY")
        points = Set(trajectory_dir).read_ints()
        data = {}
        for point in points:
            if point.ints:
                for atom, aim in point.ints.items():
                    if not atom in data.keys():
                        data[atom] = []
                    data[atom] += [aim.iqa]
        return data

    @staticmethod
    def get_trajectory_aimall_energies():
        import pandas as pd

        directories = DlpolyTools.get_trajectory_directories()
        # {
        #   MODEL001: {
        #               TIMESTEP001: {
        #                              ATOM01: -#.###,
        #                              ATOM02: -#.###,
        #                              ...
        #                            },
        #                            ...
        #             },
        #             ...
        # }
        #
        # {
        #   MODEL001: {
        #               ATOM01: [
        #                         -#.###, // TIMESTEP001
        #                         -#.###, // TIMESTEP001
        #                         ...
        #                       ],
        #                       ...
        #             },
        #             ...
        # }

        trajectories = {}
        for directory in directories:
            traj_dir = os.path.join(directory, "TRAJECTORY")
            model_name = FileTools.end_of_path(directory)
            trajectories[model_name] = df = pd.DataFrame(
                DlpolyTools.get_trajectory_aimall_energy(traj_dir)
            )

        dlpoly_dir = GLOBALS.FILE_STRUCTURE["dlpoly"]
        with pd.ExcelWriter(
            os.path.join(dlpoly_dir, "TRAJECTORY_ATM_Energies.xlsx")
        ) as writer:
            for model_name, df in trajectories.items():
                df.to_excel(writer, sheet_name=model_name)

    @staticmethod
    def get_fflux_pred_energies():
        import pandas as pd

        directories = DlpolyTools.get_trajectory_directories()
        data = {}
        for directory in directories:
            fflux_pred_file = os.path.join(directory, "FFLUX_ENERGY.txt")
            model = FileTools.end_of_path(directory)
            if os.path.isfile(fflux_pred_file):
                energies = []
                with open(fflux_pred_file, "r") as f:
                    for line in f:
                        if "Energy" in line:
                            try:
                                energies += [float(line.split()[2])]
                            except:
                                print(f"Error parsing energy from line: {line}")
                data[model] = energies
        df = pd.DataFrame(data)
        df.to_excel(
            os.path.join(str(GLOBALS.FILE_STRUCTURE["dlpoly"]), "FFLUX_Energies.xlsx")
        )

    @staticmethod
    def get_fflux_atm_energies():
        import pandas as pd

        directories = DlpolyTools.get_trajectory_directories()
        data = {}
        for directory in directories:
            fflux_atm_file = os.path.join(directory, "FFLUX_ATM_E.txt")
            model = FileTools.end_of_path(directory)
            if os.path.isfile(fflux_atm_file):
                energies = {}
                with open(fflux_atm_file, "r") as f:
                    atoms = [f"{atom}{i+1}" for i, atom in enumerate(f.readline().strip().split())]
                    for atom in atoms:
                        energies[atom] = []
                    for line in f:
                        if not atoms:
                            atoms = line.split()
                        else:
                            try:
                                for atom, energy in zip(atoms, line.strip().split()):
                                    energies[atom] += [float(energy)]
                            except:
                                print(f"Error parsing energies from line: {line}")
                data[model] = pd.DataFrame(energies)
        with pd.ExcelWriter(
            os.path.join(
                str(GLOBALS.FILE_STRUCTURE["dlpoly"]), "FFLUX_ATM_Energies.xlsx"
            )
        ) as writer:
            for model, df in data.items():
                df.to_excel(writer, sheet_name=model)

    @staticmethod
    def get_fflux_atm_forces():
        import pandas as pd

        directories = DlpolyTools.get_trajectory_directories()
        data = {}
        for directory in directories:
            fflux_atm_file = os.path.join(directory, "FFLUX_FORCES.txt")
            model = FileTools.end_of_path(directory)
            if os.path.isfile(fflux_atm_file):
                energies = {}
                with open(fflux_atm_file, "r") as f:
                    atoms = [f"{atom}{i + 1}" for i, atom in enumerate(f.readline().strip().split())]
                    for atom in atoms:
                        energies[atom] = []
                    for line in f:
                        if not atoms:
                            atoms = line.split()
                        else:
                            try:
                                for atom, energy in zip(atoms, line.strip().split()):
                                    energies[atom] += [float(energy)]
                            except:
                                print(f"Error parsing energies from line: {line}")
                data[model] = pd.DataFrame(energies)
        with pd.ExcelWriter(
                os.path.join(
                    str(GLOBALS.FILE_STRUCTURE["dlpoly"]), "FFLUX_ATM_Forces.xlsx"
                )
        ) as writer:
            for model, df in data.items():
                df.to_excel(writer, sheet_name=model)

    @staticmethod
    def refresh_traj_menu(menu):
        menu.clear_options()
        menu.add_option(
            "1",
            "Submit Trajectory to Gaussian",
            DlpolyTools.submit_trajectory_to_gaussian,
        )
        menu.add_option(
            "2", "Submit Trajectory to AIMAll", DlpolyTools.submit_trajectory_to_aimall
        )
        menu.add_space()
        menu.add_option(
            "wfn", "Get WFN Energies", DlpolyTools.get_trajectory_gaussian_energies
        )
        menu.add_option(
            "aim", "Get IQA Energies", DlpolyTools.get_trajectory_aimall_energies
        )
        menu.add_space()
        menu.add_option("r", "Auto Run ", DlpolyTools.auto_traj_analysis)
        menu.add_space()
        menu.add_option(
            "model", "Change The Model To Run Analysis On", DlpolyTools.choose_model,
        )
        menu.add_option(
            "every", "Change Number Of Points To Use", DlpolyTools.change_every
        )
        menu.add_space()
        menu.add_message(f"Use Model: {DlpolyTools.model_loc}")
        menu.add_message(f"Use Every: {DlpolyTools.use_every} Point(s) from Trajectory")
        menu.add_space()
        menu.add_option(
            "pred",
            "Get all FFLUX Predicted Energies",
            DlpolyTools.get_fflux_pred_energies,
        )
        menu.add_option(
            "atm",
            "Get all FFLUX Predicted Atom Energies",
            DlpolyTools.get_fflux_atm_energies,
        )
        menu.add_option(
            "force",
            "Get all FFLUX Predicted Atom Forces",
            DlpolyTools.get_fflux_atm_forces,
        )
        menu.add_space()
        menu.add_option("o", "Get all FFLUX Outputs", UsefulTools.not_implemented)
        menu.add_final_options()

    @staticmethod
    def traj_analysis():
        traj_menu = Menu(title="Trajectory Analysis Menu")
        traj_menu.set_refresh(DlpolyTools.refresh_traj_menu)
        traj_menu.run()

    @staticmethod
    def check_model_links():
        dlpoly_dir = GLOBALS.FILE_STRUCTURE["dlpoly"]
        log_dir = GLOBALS.FILE_STRUCTURE["log"]

        model_dirs = FileTools.get_files_in(dlpoly_dir, "*/")
        log_dirs = FileTools.get_files_in(log_dir, "*/")

        for model_dir, log_dir in zip(model_dirs, log_dirs):
            model_dir = os.path.join(model_dir, "model_krig")
            DlpolyTools.link_models(model_dir, Models(log_dir))

    @staticmethod
    def rmsd_analysis():
        opt_wfn = FileTools.get_opt(required=True)
        opt_atoms = opt_wfn._atoms
        opt_atoms.to_angstroms()
        dlpoly_dir = GLOBALS.FILE_STRUCTURE["dlpoly"]

        rmsd = []
        for model_dir in FileTools.get_files_in(dlpoly_dir, "*/"):
            trajectory_file = os.path.join(model_dir, "TRAJECTORY.xyz")
            if os.path.exists(trajectory_file):
                models = Models(os.path.join(model_dir, "model_krig"))
                n_train = models.nTrain

                trajectory = Trajectory(trajectory_file, read=True)
                rmsd += [(n_train, trajectory[-1].rmsd(opt_atoms))]

        with open("rmsd.csv", "w") as f:
            for n_train, rmsd_val in rmsd:
                f.write(f"{n_train},{rmsd_val}\n")


class CP2KTools:
    @staticmethod
    def run():
        # run checks
        # write files
        # submit
        pass

    @staticmethod
    def refresh_cp2k_menu(cp2k_menu):
        cp2k_menu.clear_options()

        cp2k_menu.add_option("r", "Run CP2K", CP2KTools.run)
        cp2k_menu.add_final_options()

    @staticmethod
    def cp2k_menu():
        # locate data files
        cp2k_menu = Menu(title="CP2K Menu")
        cp2k_menu.set_refresh(CP2KTools.refresh_cp2k_menu)
        cp2k_menu.run()
        # ? Required
        #  - Input
        #  - Temperature
        #  - Number of Iterations
        #  - DATAFILES (if not already found)
        #  - Run
        # ? Optional
        #  - Method
        #  - Basis Set
        #  - Others?


class AnalysisTools:
    @staticmethod
    def get_dir():
        t = TabCompleter()
        t.setup_completer(t.path_completer)

        ans = input("Enter Directory: ")
        if not os.path.isdir(ans):
            print("Invalid Input")
            print(f"{ans} is not a directory")
            print()
        else:
            return ans

    @staticmethod
    def set_dir(directory=None):
        while not directory:
            directory = AnalysisTools.get_dir()
        return directory

    @staticmethod
    def set_output_file(default="output"):
        allowed_filetypes = [".xlsx", ".xls"]
        outfile = UsefulTools.input_with_prefill(
            "Enter Output File: ", S_CurveTools.output_file
        )
        if outfile == "":
            outfile = default
        elif not any(outfile.endswith(filetype) for filetype in allowed_filetypes):
            outfile += ".xlsx"
        return outfile


class S_CurveTools(AnalysisTools):
    vs_loc = ""
    sp_loc = ""

    log_loc = ""
    model_loc = ""

    validation_set = ""
    models = ""

    submit = False
    output_file = "s_curves.xlsx"

    # TODO - Natural Sort Column Headings
    @staticmethod
    def _calculate_s_curves(validation_set, models, property):
        model_data = {}
        predictions = models.predict(
            validation_set, atoms=True, type=property, verbose=True
        )
        for point, prediction in zip(validation_set, predictions):
            for model_name, model_prediction in prediction.items():
                if model_name not in model_data.keys():
                    model_data[model_name] = {}
                for atom, int_data in point.ints.items():
                    if atom not in model_data[model_name].keys():
                        model_data[model_name][atom] = {
                            "true": [],
                            "predicted": [],
                            "error": [],
                        }

                    true_value = int_data.get_property(model_name)

                    predicted_value = model_prediction[int_data.num]
                    error = np.abs(true_value - predicted_value)
                    if model_name.lower() == "iqa":
                        error *= Constants.ha_to_kj_mol

                    model_data[model_name][atom]["true"].append(true_value)
                    model_data[model_name][atom]["predicted"].append(predicted_value)
                    model_data[model_name][atom]["error"].append(error)
        return model_data

    @staticmethod
    def add_percentage_column(df):
        percentages = [100 * (i + 1) / len(df) for i in range(len(df))]
        df["%"] = percentages
        return df

    @staticmethod
    def to_df(property, data):
        import pandas as pd

        atom_data = {}
        errors = {}
        for atom, data in data.items():
            property_df = pd.DataFrame(data)
            errors[atom] = data["error"]
            property_df.sort_values(by="error", inplace=True)
            property_df = S_CurveTools.add_percentage_column(property_df)
            atom_data[atom + "_" + property] = property_df
        errors_df = pd.DataFrame(errors)
        errors_df.loc[:, "Total"] = errors_df.sum(axis=1)
        errors_df.sort_values(by="Total", inplace=True)
        errors_df = S_CurveTools.add_percentage_column(errors_df)
        atom_data["Total_" + property] = errors_df
        return atom_data

    @staticmethod
    @UsefulTools.external_function()
    def calculate_s_curves(
        predict_property="all", validation_set=None, models=None, output_file=None,
    ):
        import pandas as pd

        if validation_set is None:
            validation_set = S_CurveTools.validation_set
        if models is None:
            models = S_CurveTools.models
        if output_file is None:
            output_file = S_CurveTools.output_file

        if S_CurveTools.submit:
            AutoTools.submit_ichor_s_curves(
                predict_property, validation_set, models, output_file
            )

        print("Reading Data")
        validation_set = Set(validation_set).read()
        models = Models(models, read_models=True)
        print()

        print("Making Predictions")
        atom_data = {}
        s_curve_data = S_CurveTools._calculate_s_curves(
            validation_set, models, predict_property
        )
        for property, atom_property_data in s_curve_data.items():
            atom_data.update(S_CurveTools.to_df(property, atom_property_data))

        with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
            for df_name, df in atom_data.items():
                df.to_excel(writer, sheet_name=df_name)

    @staticmethod
    def toggle_submit():
        S_CurveTools.submit = not S_CurveTools.submit

    @staticmethod
    def change_output_file():
        S_CurveTools.output_file = AnalysisTools.set_output_file(S_CurveTools.output_file)

    @staticmethod
    def set_vs_dir(directory=None):
        S_CurveTools.validation_set = AnalysisTools.set_dir(directory)

    @staticmethod
    def set_model_dir(directory=None):
        S_CurveTools.models = AnalysisTools.set_dir(directory)

    @staticmethod
    def set_model_from_log():
        log_menu = Menu(title="Select Model From Log", auto_close=True)
        for i, model in enumerate(FileTools.get_files_in(S_CurveTools.log_loc, "*/")):
            log_menu.add_option(
                f"{i+1}",
                model,
                S_CurveTools.set_model_dir,
                kwargs={"directory": model},
            )
        log_menu.add_final_options(exit=False)
        log_menu.run()

    @staticmethod
    def refresh_vs_menu(menu):
        menu.clear_options()
        menu.add_option(
            "1",
            f"Validation Set ({S_CurveTools.vs_loc})",
            S_CurveTools.set_vs_dir,
            kwargs={"directory": S_CurveTools.vs_loc},
        )
        menu.add_option(
            "2",
            f"Sample Pool ({S_CurveTools.sp_loc})",
            S_CurveTools.set_vs_dir,
            kwargs={"directory": S_CurveTools.sp_loc},
        )
        menu.add_option("3", "Custom Directory", S_CurveTools.set_vs_dir)
        menu.add_space()
        menu.add_message(f"Validation Set Location: {S_CurveTools.validation_set}")
        menu.add_final_options(exit=False)

    @staticmethod
    def refresh_model_menu(menu):
        menu.clear_options()
        menu.add_option(
            "1",
            f"Current Model ({S_CurveTools.model_loc})",
            S_CurveTools.set_model_dir,
            kwargs={"directory": str(GLOBALS.FILE_STRUCTURE["models"])},
        )
        menu.add_option(
            "2",
            f"Choose From LOG ({S_CurveTools.log_loc})",
            S_CurveTools.set_model_from_log,
        )
        menu.add_option("3", "Custom Directory", S_CurveTools.set_model_dir)
        menu.add_space()
        menu.add_message(f"Model Location: {S_CurveTools.models}")
        menu.add_final_options(exit=False)

    @staticmethod
    def refresh_s_curve_menu(menu):
        vs_menu = Menu(title="Select Validation Set", auto_close=True)
        vs_menu.set_refresh(S_CurveTools.refresh_vs_menu)

        model_menu = Menu(title="Select Model Location", auto_close=True)
        model_menu.set_refresh(S_CurveTools.refresh_model_menu)

        menu.clear_options()
        menu.add_option(
            "1",
            "Calculate IQA S-Curves",
            S_CurveTools.calculate_s_curves,
            kwargs={"predict_property": "iqa"},
        )
        menu.add_option(
            "2",
            "Calculate Multipole S-Curves",
            S_CurveTools.calculate_s_curves,
            kwargs={"predict_property": "multipoles"},
        )
        menu.add_option(
            "3",
            "Calculate All S-Curves",
            S_CurveTools.calculate_s_curves,
            kwargs={"predict_property": "all"},
        )
        menu.add_space()
        menu.add_option("vs", "Select Validation Set Location", vs_menu.run)
        menu.add_option("model", "Select Model Location", model_menu.run)
        menu.add_option("output", "Change Output File", S_CurveTools.change_output_file)
        menu.add_option(
            "submit", "Toggle Submit To Cluster", S_CurveTools.toggle_submit
        )
        menu.add_space()
        menu.add_message(f"Validation Set Location: {S_CurveTools.validation_set}")
        menu.add_message(f"Model Location: {S_CurveTools.models}")
        menu.add_space()
        menu.add_message(f"Output File: {S_CurveTools.output_file}")
        menu.add_message(f"Submit To Cluster: {S_CurveTools.submit}")
        menu.add_final_options()

    @staticmethod
    def run():
        S_CurveTools.vs_loc = GLOBALS.FILE_STRUCTURE["validation_set"]
        S_CurveTools.sp_loc = GLOBALS.FILE_STRUCTURE["sample_pool"]

        S_CurveTools.model_loc = GLOBALS.FILE_STRUCTURE["models"]
        S_CurveTools.log_loc = GLOBALS.FILE_STRUCTURE["log"]

        S_CurveTools.validation_set = S_CurveTools.vs_loc
        S_CurveTools.models = S_CurveTools.model_loc

        s_curves_menu = Menu(title="S-Curves Menu")
        s_curves_menu.set_refresh(S_CurveTools.refresh_s_curve_menu)
        s_curves_menu.run()


class RecoveryErrorTools:
    property_ = "iqa"

    @staticmethod
    def calculate_recovery_errors_iqa(directory):
        import pandas as pd

        points = Set(directory).read()

        iqa_energies = {}
        wfn_energies = []
        for point in points:
            if point.wfn.energy != 0:
                wfn_energies += [point.wfn.energy]
            for int_atom, int_data in point.ints.items():
                if int_atom not in iqa_energies.keys():
                    iqa_energies[int_atom] = []
                iqa_energies[int_atom] += [int_data.eiqa]

        df = pd.DataFrame(iqa_energies)
        df.columns = UsefulTools.natural_sort(list(df.columns))
        df.loc[:, "Total"] = df.sum(axis=1)
        df["WFN"] = pd.to_numeric(wfn_energies, errors="coerce")

        df["error / Ha"] = (df["Total"] - df["WFN"]).abs()
        df["error / kJ/mol"] = df["error / Ha"] * Constants.ha_to_kj_mol
        df.to_excel("IQA_Recovery_Errors.xlsx")

        return stats.describe(df["error / kJ/mol"]), "kJ/mol"

    @staticmethod
    def calculate_recovery_errors_charge(directory):
        import pandas as pd

        points = Set(directory).read_ints().read_gau()

        gaussian_charges = []
        atom_charges = {}
        for point in points:
            if point.gau.charge != None:
                gaussian_charges += [point.gau.charge]
            for int_atom, int_data in point.ints.items():
                if int_atom not in atom_charges.keys():
                    atom_charges[int_atom] = []
                atom_charges[int_atom] += [int_data.q]

        df = pd.DataFrame(atom_charges)
        df.columns = UsefulTools.natural_sort(list(df.columns))
        df.loc[:, "Total"] = df.sum(axis=1)
        df["Gaussian"] = pd.to_numeric(gaussian_charges, errors="coerce")

        df["error / electrons"] = (df["Total"] - df["Gaussian"]).abs()
        df.to_excel("Charges_Recovery_Errors.csv")

        return stats.describe(df["error / electrons"]), "electrons"

    @staticmethod
    def calculate_recovery_errors_dipole(directory):
        UsefulTools.not_implemented()
        # import pandas as pd

        # points = Set(directory).read_ints().read_gau()

        # gaussian_dipoles = []
        # atom_dipoles = {}
        # for point in points:
        #     if point.gau.dipole != {}:
        #         gaussian_charges += [point.gau.charge]
        #     for int_atom, int_data in point.ints.items():
        #         if int_atom not in atom_charges.keys():
        #             atom_charges[int_atom] = []
        #         atom_charges[int_atom] += [int_data.q]
        #
        # df = pd.DataFrame(atom_charges)
        # df.columns = UsefulTools.natural_sort(list(df.columns))
        # df.loc[:, "Total"] = df.sum(axis=1)
        # df["Gaussian"] = pd.to_numeric(gaussian_charges, errors="coerce")
        #
        # df["error / electrons"] = (df["Total"] - df["Gaussian"]).abs()
        # df.to_xlsx("Charges_Recovery_Errors.csv")

        # return stats.describe(df["error / electrons"]), "electrons"


    @staticmethod
    def calculate_recovery_errors(directory):
        property_function = {
            "iqa": RecoveryErrorTools.calculate_recovery_errors_iqa,
            "charge": RecoveryErrorTools.calculate_recovery_errors_charge,
            "dipole": RecoveryErrorTools.calculate_recovery_errors_dipole
        }

        result, unit = property_function[RecoveryErrorTools.property_](directory)

        print()
        print("#############################")
        print("# Recovery Error Statistics #")
        print("#############################")
        print()
        print(f"Min:  {result.minmax[0]:.6f} {unit}")
        print(f"Max:  {result.minmax[1]:.6f} {unit}")
        print(f"Mean: {result.mean:.6f} {unit}")
        print(f"Var:  {result.variance:.6f} {unit}")
        print()

    # TODO - Implement switch property
    @staticmethod
    def recovery_error_menu_refresh(menu):
        ts_dir = GLOBALS.FILE_STRUCTURE["training_set"]
        sp_dir = GLOBALS.FILE_STRUCTURE["sample_pool"]
        vs_dir = GLOBALS.FILE_STRUCTURE["validation_set"]

        menu.add_option(
            "1",
            "Calculate Recovery Errors of Training Set",
            RecoveryErrorTools.calculate_recovery_errors,
            kwargs={"directory": ts_dir},
            wait=True,
        )
        menu.add_option(
            "2",
            "Calculate Recovery Errors of Sample Pool",
            RecoveryErrorTools.calculate_recovery_errors,
            kwargs={"directory": sp_dir},
            wait=True,
        )
        menu.add_option(
            "3",
            "Calculate Recovery Errors of Validation Set",
            RecoveryErrorTools.calculate_recovery_errors,
            kwargs={"directory": vs_dir},
            wait=True,
        )
        menu.add_space()
        menu.add_option("c", "Change Property to Calculate Recovery Error", UsefulTools.not_implemented)
        menu.add_space()
        menu.add_message(f"Property to Calculate Recovery Error: {RecoveryErrorTools.property_}")
        menu.add_final_options()

    @staticmethod
    def recovery_error_menu():
        error_menu = Menu(title="Recovery Error Menu", auto_close=True)
        error_menu.set_refresh(RecoveryErrorTools.recovery_error_menu_refresh)
        error_menu.run()


class RMSETools(AnalysisTools):
    validation_set = ""
    models = "all"
    output_file = "rmse.xlsx"
    submit = False

    vs_loc = ""
    sp_loc = ""

    @staticmethod
    def make_models_list(loc):
        if loc.lower() == "all":
            models_loc = [d for d in Path(GLOBALS.FILE_STRUCTURE["log"]).iterdir() if d.is_dir()]
        else:
            models_loc = [loc]
        return [Models(loc, read_models=True) for loc in models_loc]

    @staticmethod
    def calculate_rmse(type="iqa"):
        models_list = RMSETools.make_models_list(RMSETools.models)
        vs = Set(RMSETools.validation_set).read()
        rmse_data = {}
        for models in models_list:
            predictions = models.predict(vs, atoms=True, type=type, verbose=True)
            rmse_data[models.nTrain] = {}
            for point, predicted in zip(vs, predictions):
                for type, values in predicted.items():
                    true_total = 0.0
                    pred_total = 0.0
                    for atom, pred in values.items():
                        atom_name = point.ints[atom - 1].atom
                        if not atom_name + "_True" in rmse_data[models.nTrain].keys():
                            rmse_data[models.nTrain][atom_name + "_True"] = []
                            rmse_data[models.nTrain][atom_name + "_Predicted"] = []
                            rmse_data[models.nTrain][atom_name + "_Error"] = []
                        true = getattr(point.ints[atom - 1], type)
                        true_total += true
                        pred_total += pred
                        rmse_data[models.nTrain][atom_name + "_True"] += [true]
                        rmse_data[models.nTrain][atom_name + "_Predicted"] += [pred]
                        error = np.abs(true - pred) * (Constants.ha_to_kj_mol if type == "iqa" else 1.0)
                        rmse_data[models.nTrain][atom_name + "_Error"] += [error]
                    if not "Total_True" in rmse_data[models.nTrain].keys():
                        rmse_data[models.nTrain]["Total_True"] = []
                        rmse_data[models.nTrain]["Total_Predicted"] = []
                        rmse_data[models.nTrain]["Total_Error"] = []
                    rmse_data[models.nTrain]["Total_True"] += [true_total]
                    rmse_data[models.nTrain]["Total_Predicted"] += [pred_total]
                    error = np.abs(true_total - pred_total) * (Constants.ha_to_kj_mol if type == "iqa" else 1.0)
                    rmse_data[models.nTrain]["Total_Error"] += [error]

        rmse_data = {n: d for n, d in sorted(rmse_data.items(), key=lambda item: item[0])}

        def rmse(data):
            total = sum(x**2 for x in data)
            return np.sqrt(total/len(data))

        rmse_calc = {}
        for n_train, data in rmse_data.items():
            rmse_calc[n_train] = {}
            for heading, values in data.items():
                if "_Error" in heading:
                    rmse_calc[n_train][heading.split("_")[0]] = rmse(values)

        import pandas as pd
        with pd.ExcelWriter(RMSETools.output_file) as writer:
            df = pd.DataFrame(rmse_calc)
            df.T.to_excel(writer, sheet_name="RMSE")

            for n_train, data in rmse_data.items():
                df = pd.DataFrame(data).sort_values("Total_Error")
                df.to_excel(writer, sheet_name=f"{n_train} Points")


    @staticmethod
    def toggle_submit():
        RMSETools.submit = not RMSETools.submit

    @staticmethod
    def change_output_file():
        RMSETools.output_file = AnalysisTools.set_output_file(S_CurveTools.output_file)

    @staticmethod
    def set_vs_dir(directory=None):
        RMSETools.validation_set = AnalysisTools.set_dir(directory)

    @staticmethod
    def set_model_dir(directory=None):
        RMSETools.models = AnalysisTools.set_dir(directory)

    @staticmethod
    def refresh_vs_menu(menu):
        menu.clear_options()
        menu.add_option(
            "1",
            f"Validation Set ({RMSETools.vs_loc})",
            RMSETools.set_vs_dir,
            kwargs={"directory": RMSETools.vs_loc},
        )
        menu.add_option(
            "2",
            f"Sample Pool ({RMSETools.sp_loc})",
            RMSETools.set_vs_dir,
            kwargs={"directory": RMSETools.sp_loc},
        )
        menu.add_option("3", "Custom Directory", RMSETools.set_vs_dir)
        menu.add_space()
        menu.add_message(f"Validation Set Location: {RMSETools.validation_set}")
        menu.add_final_options(exit=False)

    @staticmethod
    def refresh_model_menu(menu):
        menu.clear_options()
        menu.add_option(
            "1",
            f"Current Model ({S_CurveTools.model_loc})",
            RMSETools.set_model_dir,
            kwargs={"directory": str(GLOBALS.FILE_STRUCTURE["models"])},
        )
        menu.add_option(
            "2",
            f"Choose From LOG ({S_CurveTools.log_loc})",
            S_CurveTools.set_model_from_log,
        )
        menu.add_option("3", "Custom Directory", RMSETools.set_model_dir)
        menu.add_space()
        menu.add_option("a", "All Models from LOG", RMSETools.set_model_dir, kwargs={"directory": "all"})
        menu.add_space()
        menu.add_message(f"Model Location: {S_CurveTools.models}")
        menu.add_final_options(exit=False)

    @staticmethod
    def refresh_rmse_menu(menu):
        vs_menu = Menu(title="Select Validation Set", auto_close=True)
        vs_menu.set_refresh(RMSETools.refresh_vs_menu)

        model_menu = Menu(title="Select Model Location", auto_close=True)
        model_menu.set_refresh(RMSETools.refresh_model_menu)

        menu.add_option("1", "Calculate RMSE of IQA Model(s)", RMSETools.calculate_rmse, kwargs={"type": "iqa"})
        menu.add_option("2", "Calculate RMSE of Multipole Model(s)", RMSETools.calculate_rmse, kwargs={"type": "multipoles"})
        menu.add_option("3", "Calculate RMSE of All Model(s)", RMSETools.calculate_rmse, kwargs={"type": "all"})
        menu.add_space()
        menu.add_option("vs", "Select Validation Set Location", vs_menu.run)
        menu.add_option("model", "Select Model Location", model_menu.run)
        menu.add_option("output", "Change Output File", RMSETools.change_output_file)
        # menu.add_option(
        #     "submit", "Toggle Submit To Cluster", RMSETools.toggle_submit
        # )
        menu.add_space()
        menu.add_message(f"Validation Set Location: {RMSETools.validation_set}")
        menu.add_message(f"Model Location: {RMSETools.models}")
        menu.add_space()
        menu.add_message(f"Output File: {RMSETools.output_file}")
        # menu.add_message(f"Submit To Cluster: {RMSETools.submit}")
        menu.add_final_options()

    @staticmethod
    def rmse_menu():
        RMSETools.vs_loc = str(GLOBALS.FILE_STRUCTURE["validation_set"])
        RMSETools.sp_loc = str(GLOBALS.FILE_STRUCTURE["sample_pool"])
        RMSETools.validation_set = RMSETools.vs_loc

        rmse_menu = Menu(title="RMSE Menu")
        rmse_menu.set_refresh(RMSETools.refresh_rmse_menu)
        rmse_menu.run()


class SetupTools:
    sets = ["training_set", "sample_pool", "validation_set"]

    @staticmethod
    def directories():
        for directory in SetupTools.sets:
            dir_path = GLOBALS.FILE_STRUCTURE[directory]
            empty = False
            if UsefulTools.check_bool(input(f"Setup Directory: {dir_path} [Y/N]")):
                if os.path.isdir(dir_path):
                    print()
                    print(f"Warning: {dir_path} exists")
                    empty = UsefulTools.check_bool(
                        input(f"Would you like to empty {dir_path}? [Y/N]")
                    )
                FileTools.mkdir(dir_path, empty=empty)
            print()

    @staticmethod
    def make_set(set_to_make, points):
        set_name = UsefulTools.prettify_string(set_to_make)
        n_points = -1
        if set_to_make != "training_set":
            while True:
                n_points = int(input(f"Enter number of points for the {set_name}: "))
                if n_points > 0:
                    break
                else:
                    print("Error: Number of points must be greater than 0")
        points.make_set(n_points, GLOBALS.FILE_STRUCTURE[set_to_make])
        return points

    # TODO - Points -> Set
    @staticmethod
    def make_sets():
        t = TabCompleter()
        t.setup_completer(t.path_completer)
        set_location = input(
            "Enter XYZ file or Directory containing the Points to use: "
        )
        t.remove_completer()

        # append data source to file

        points = Points()
        points.read_set(set_location)

        for set_to_make in SetupTools.sets:
            set_name = UsefulTools.prettify_string(set_to_make)
            print()
            ans = input(f"Would you like to make set: {set_name} [Y/N]")
            if UsefulTools.check_bool(ans):
                points = SetupTools.make_set(set_to_make, points)


class SettingsTools:
    edit_var = None
    show_hidden = False

    @staticmethod
    def set_default():
        GLOBALS.set(SettingsTools.edit_var.name, SettingsTools.edit_var.default)

    @staticmethod
    def set_value(value):
        SettingsTools.edit_var.value = value

    @staticmethod
    def edit_value():
        print(f"Edit {SettingsTools.edit_var.name}")
        while True:
            new_value = UsefulTools.input_with_prefill(
                ">> ", SettingsTools.edit_var.value
            )
            try:
                SettingsTools.edit_var.value = new_value
                break
            except:
                print(
                    f"Value Error: Must be of type {SettingsTools.edit_var.type.__name__}"
                )

    @staticmethod
    def choose_value():
        choose_menu = Menu(
            title=f"{SettingsTools.edit_var.name} Allowed Values", auto_close=True,
        )
        for i, allowed_value in enumerate(SettingsTools.edit_var.allowed_values):
            choose_menu.add_option(
                str(i + 1),
                str(allowed_value),
                SettingsTools.set_value,
                kwargs={"value": allowed_value},
            )
        choose_menu.add_final_options()
        choose_menu.run()

    @staticmethod
    def refresh_setting_menu(menu):
        menu.clear_options()
        menu.add_message(f"Value:   {SettingsTools.edit_var.value}")
        menu.add_space()
        menu.add_message(f"Type:    {SettingsTools.edit_var.type.__name__}")
        menu.add_message(f"Default: {SettingsTools.edit_var.default}")
        menu.add_space()
        # menu.add_message(f"Hidden:  {SettingsTools.edit_var.hidden}")
        # menu.add_message(f"Changed: {SettingsTools.edit_var.changed}")
        menu.add_option("e", "Edit value of setting", SettingsTools.edit_value)
        menu.add_option("d", "Revert to default value", SettingsTools.set_default)
        if SettingsTools.edit_var.allowed_values:
            menu.add_option(
                "c", "Choose from allowed values", SettingsTools.choose_value
            )
        menu.add_final_options()

    @staticmethod
    def save_changes():
        GLOBALS.save_to_config()

    @staticmethod
    def change_config():
        filetypes = [".properties", ".yaml"]
        print(f"Change config file")
        while True:
            new_config = UsefulTools.input_with_prefill(">> ", Arguments.config_file)
            if any(new_config.endswith(filetype) for filetype in filetypes):
                Arguments.config_file = new_config
                break
            else:
                print("Error: Unknwon Filetype")
                print("Known filetypes: {filetypes}")

    @staticmethod
    def toggle_hidden():
        SettingsTools.show_hidden = not SettingsTools.show_hidden

    @staticmethod
    def refresh_settings_menu(menu):
        menu.clear_options()
        global_variables = GLOBALS.items(show_hidden=SettingsTools.show_hidden)
        for global_var in global_variables:
            if not global_var.hidden:
                global_var_value = "= " + str(global_var.value)
                menu.add_option(
                    global_var.name,
                    global_var_value,
                    SettingsTools.change,
                    kwargs={"var": global_var},
                )
        menu.add_space()
        if SettingsTools.show_hidden:
            for global_var in global_variables:
                if global_var.hidden:
                    global_var_value = str(global_var.value)
                    menu.add_message(global_var.name + " = " + global_var_value)
            menu.add_space()

        menu.add_option(
            "s",
            f"Save changes to config ({Arguments.config_file})",
            SettingsTools.save_changes,
        )
        menu.add_option("c", "Change config file", SettingsTools.change_config)
        menu.add_option("h", "Show/Hide Hidden Variables", SettingsTools.toggle_hidden)
        menu.add_final_options()

    @staticmethod
    def change(var):
        SettingsTools.edit_var = var
        setting_menu = Menu(title=f"Edit {var.name}", auto_close=True)
        setting_menu.set_refresh(SettingsTools.refresh_setting_menu)
        setting_menu.run()

    @staticmethod
    def show():
        settings_menu = Menu(title="Settings Menu")
        settings_menu.set_refresh(SettingsTools.refresh_settings_menu)
        settings_menu.run()


class ModelTools:
    training_set_directory = ""
    training_set = Set()
    n_training_points = 0

    multipole_model = "all"

    submit = False

    @staticmethod
    def make_models_submit(directory, model_type, npoints):
        return AutoTools.run_models(directory, model_type, npoints)

    @staticmethod
    @UsefulTools.external_function()
    def make_models(directory, model_type, npoints=-1):
        if ModelTools.submit:
            ModelTools.make_models_submit(directory, model_type, npoints)
            return

        npoints = int(npoints)
        if npoints < 0:
            ModelTools.init(directory)
            npoints = ModelTools.n_training_points

        if model_type.lower() == "all":
            model_type = "multipoles"
        GLOBALS.LOG_WARNINGS = True
        GLOBALS.IQA_MODELS = model_type.lower() == "iqa"

        logger.info(f"Making {model_type} models")

        aims = Set(directory).read()
        models = aims.make_training_set(model_type, npoints)
        SubmissionTools.make_ferebus_script(models, model_type=model_type)

    @staticmethod
    def choose_multipole(multipole):
        ModelTools.multipole_model = multipole

    @staticmethod
    def choose_multipole_model():
        multipole_menu = Menu(title="Choose Multipole Menu", auto_close=True)

        for multipole_name in Constants.multipole_names:
            multipole_menu.add_option(
                f"{multipole_name}",
                f"{multipole_name} Multipole Moment",
                ModelTools.choose_multipole,
                kwargs={"multipole": multipole_name},
            )

        multipole_menu.add_space()
        multipole_menu.add_option(
            "all",
            "All Multipole Moments",
            ModelTools.choose_multipole,
            kwargs={"multipole": "all"},
        )
        multipole_menu.add_final_options()
        multipole_menu.run()

    @staticmethod
    def change_n_points():
        print(f"Enter Number of Training Points (1 - {len(ModelTools.training_set)})")
        while True:
            ans = input(">> ")
            try:
                ans = int(ans)
                if 1 <= ans <= len(ModelTools.training_set):
                    ModelTools.n_training_points = ans
                    return
                else:
                    print(
                        "Error: Number of points must be in the range 1 - {len(ModelTools.training_set)}"
                    )
            except:
                print("Error: Answer must be an integer")

    @staticmethod
    def toggle_submit():
        ModelTools.submit = not ModelTools.submit

    @staticmethod
    def refresh_make_models(menu):
        model_types = {
            "IQA": "iqa",
            "Multipoles": ModelTools.multipole_model,
        }

        menu.clear_options()
        for i, (model_name, model_type) in enumerate(model_types.items()):
            menu.add_option(
                f"{i+1}",
                model_name,
                ModelTools.make_models,
                kwargs={
                    "directory": ModelTools.training_set_directory,
                    "model_type": model_type,
                    "npoints": ModelTools.n_training_points,
                },
            )
        menu.add_space()
        menu.add_option(
            "m", "Choose Multipole Model", ModelTools.choose_multipole_model,
        )
        menu.add_option(
            "c", "Change Number of Training Points", ModelTools.change_n_points
        )
        menu.add_option("s", "Toggle Submit", ModelTools.toggle_submit)
        menu.add_space()
        menu.add_message(f"Multipole Model: {ModelTools.multipole_model}")
        menu.add_message(f"Number of Training Points: {ModelTools.n_training_points}")
        menu.add_message(f"Submit Model Making: {ModelTools.submit}")
        menu.add_final_options()

    @staticmethod
    def init(directory):
        ModelTools.training_set_directory = directory
        ModelTools.training_set = Set(ModelTools.training_set_directory)
        ModelTools.n_training_points = len(ModelTools.training_set)

    @staticmethod
    def make_models_menu(directory):
        ModelTools.init(directory)

        model_menu = Menu(title="Model Menu")
        model_menu.set_refresh(ModelTools.refresh_make_models)
        model_menu.run()


class FileRemoverDaemon(Daemon):
    def __init__(self):
        cwd = os.getcwd()
        pidfile = os.path.join(cwd, GLOBALS.FILE_STRUCTURE["file_remover_pid"])
        stdout = os.path.join(cwd, GLOBALS.FILE_STRUCTURE["file_remover_stdout"])
        stderr = os.path.join(cwd, GLOBALS.FILE_STRUCTURE["file_remover_stderr"])
        super().__init__(pidfile, stdout=stdout, stderr=stderr)

    def run(self):
        FileRemover.run()
        self.stop()


class FileRemover:
    @staticmethod
    def remove_core():
        print("Removing Core Files (.core)\n")
        for entry in os.listdir():
            if os.path.isfile(entry) and re.match(r"core\.\d+", entry):
                filesize = Path(entry).stat().st_size
                print(f"Deleted: {entry} ({filesize} bytes)")
                os.remove(entry)

    @staticmethod
    def run():
        FileRemover.remove_core()

    @staticmethod
    def run_daemon():
        FileTools.mkdir(GLOBALS.FILE_STRUCTURE["file_remover_daemon"], empty=True)
        file_remover_daemon = FileRemoverDaemon()
        file_remover_daemon.start()


class SetTools:
    @staticmethod
    def to_csv(directory):
        points = Set(directory).read()
        data = {}
        for point in points:
            point.atoms.calculate_features()
            for atom in point:
                atom_name = atom.atom_num
                atom_features = atom.features
                outputs = Constants.multipole_names + ["iqa"]
                atom_output = {output: point.ints[atom_name].get_property(output) for output in outputs}
                if atom_name not in data.keys():
                    data[atom_name] = {}

                for i, input in enumerate(atom_features):
                    feature_name = f"f{i+1}"
                    if feature_name not in data[atom_name].keys():
                        data[atom_name][feature_name] = []
                    data[atom_name][feature_name] += [input]

                for output_name, output in atom_output.items():
                    if output_name not in data[atom_name].keys():
                        data[atom_name][output_name] = []
                    data[atom_name][output_name] += [output]

        import pandas as pd
        for atom, atom_data in data.items():
            df = pd.DataFrame(atom_data)
            directory_name = directory.replace(os.sep, "_").strip("_").upper()
            df.to_csv(f"{atom}_{directory_name}.csv")

    @staticmethod
    def to_csv_menu():
        ts_dir = GLOBALS.FILE_STRUCTURE["training_set"]
        sp_dir = GLOBALS.FILE_STRUCTURE["sample_pool"]
        vs_dir = GLOBALS.FILE_STRUCTURE["validation_set"]

        csv_menu = Menu(title="CSV Menu")
        csv_menu.add_option("1", "Training Set", SetTools.to_csv, {"directory": ts_dir})
        csv_menu.add_option("2", "Sample Pool", SetTools.to_csv, {"directory": sp_dir})
        csv_menu.add_option("3", "Validation Set", SetTools.to_csv, {"directory": vs_dir})
        csv_menu.add_final_options()

        csv_menu.run()

#############################################
#            Function Definitions           #
#############################################


def _ssh(machine):
    global SSH_SETTINGS

    ssh = SSH(machine)
    ssh.connect()

    ssh.open()

    logout_commands = ["logout", "quit", "exit", "close"]
    select_commands = ["select", "here", "run"]
    while True:
        command = input(">> ")
        if command in logout_commands:
            break
        elif command in select_commands:
            SSH_SETTINGS["machine"] = machine.upper()
            SSH_SETTINGS["working_directory"] = ssh.pwd
            SSH_SETTINGS["username"] = ssh.username
            SSH_SETTINGS["password"] = ssh.password
            break
        ssh.execute(command)
    ssh.close()
    return Menu.CLOSE


def ssh():
    ssh_menu = Menu(title="SSH Menu")
    for i, machine in enumerate(EXTERNAL_MACHINES.keys()):
        ssh_menu.add_option(
            f"{i+1}",
            machine.upper(),
            _ssh,
            kwargs={"machine": machine},
            auto_close=True,
        )
    ssh_menu.add_final_options()
    ssh_menu.run()


@UsefulTools.external_function()
def log_time(*args):
    timing_logger.info(" | ".join([str(arg) for arg in args]))


@UsefulTools.external_function()
def submit_gjfs(directory):
    logger.info("Submitting gjfs to Gaussian")
    gjfs = Set(directory).read_gjfs()
    gjfs.format_gjfs()
    return gjfs.submit_gjfs()


@UsefulTools.external_function()
def submit_wfns(directory):
    logger.info("Submitting wfns to AIMAll")
    wfns = Set(directory).read_gjfs().read_wfns()
    wfns.submit_wfns()


@UsefulTools.external_function()
def move_models(model_file, model_type="iqa", copy_to_log=True):
    logger.info("Moving Completed Models")
    model_directory = GLOBALS.FILE_STRUCTURE["models"]
    FileTools.mkdir(model_directory)

    model_files = [model_file]
    if os.path.isdir(model_file):
        model_files = FileTools.get_files_in(model_file, "*_kriging_*.txt")

    for model_file in model_files:
        model = Model(model_file)
        model.remove_no_noise()

        if model_type.lower() == "iqa":
            model.type = "IQA"
        elif not model_type.lower() == "multipoles":
            model.type = str(model_type)
        new_model_file = model.get_fname(model_directory)
        FileTools.copy_file(model_file, new_model_file)

        if copy_to_log:
            model.copy_to_log()


@UsefulTools.external_function()
def calculate_errors(models_directory, sample_pool_directory):
    logger.info("Calculating errors of the Sample Pool")

    models = Models(models_directory, read_models=True)
    sample_pool = Set(sample_pool_directory).read_gjfs()

    points = models.expected_improvement(sample_pool)

    if GLOBALS.SUBMITTED:
        move_points = True
    else:
        move_points = UsefulTools.check_bool(
            input("Would you like to move points to Training Set? [Y/N]")
        )

    if move_points:
        logger.info("Moving points to the Training Set")
        training_set = Set(GLOBALS.FILE_STRUCTURE["training_set"])
        training_set = training_set | points
        training_set.format_gjfs()


def dlpoly_analysis():
    dlpoly_menu = Menu(title="DLPOLY Menu")
    dlpoly_menu.add_option("1", "Run DLPOLY on LOG", DlpolyTools.run_on_log)
    dlpoly_menu.add_option(
        "2", "Run DLPOLY on current models", DlpolyTools.run_on_model
    )
    dlpoly_menu.add_space()
    dlpoly_menu.add_option(
        "g",
        "Calculate Gaussian Energies",
        DlpolyTools.calculate_gaussian_energies,
        wait=True,
    )
    dlpoly_menu.add_option(
        "wfn", "Get WFN Energies", DlpolyTools.get_wfn_energies, wait=True
    )
    dlpoly_menu.add_space()
    dlpoly_menu.add_option(
        "rmsd", "Calculate RMSD to Gaussian Minimum", DlpolyTools.rmsd_analysis
    )
    dlpoly_menu.add_option(
        "traj", "Trajectory Analysis Tools", DlpolyTools.traj_analysis
    )
    dlpoly_menu.add_space()
    dlpoly_menu.add_option("r", "Auto Run DLPOLY Analysis", DlpolyTools.auto_run)
    dlpoly_menu.add_option(
        "link", "Check Model Symlinks", DlpolyTools.check_model_links, hidden=True,
    )
    dlpoly_menu.add_final_options()

    dlpoly_menu.run()


def opt():
    sp_dir = GLOBALS.FILE_STRUCTURE["sample_pool"]
    atoms = GJF(FileTools.get_first_gjf(sp_dir)).read().atoms

    opt_dir = GLOBALS.FILE_STRUCTURE["opt"]
    FileTools.mkdir(opt_dir)

    opt_gjf = GJF(os.path.join(opt_dir, GLOBALS.SYSTEM_NAME + "1".zfill(4) + ".gjf"))
    opt_gjf._atoms = atoms
    opt_gjf.job_type = "opt"
    opt_gjf.write()
    opt_gjf.submit()


#############################################
#                 Main Loop                 #
#############################################


def main_menu():
    ts_dir = GLOBALS.FILE_STRUCTURE["training_set"]
    sp_dir = GLOBALS.FILE_STRUCTURE["sample_pool"]
    vs_dir = GLOBALS.FILE_STRUCTURE["validation_set"]
    models_dir = GLOBALS.FILE_STRUCTURE["models"]

    # === Training Set Menu ===#
    training_set_menu = Menu(title="Training Set Menu")
    training_set_menu.add_option(
        "1", "Submit GJFs to Gaussian", submit_gjfs, kwargs={"directory": ts_dir},
    )
    training_set_menu.add_option(
        "2",
        "Submit WFNs to AIMAll",
        submit_wfns,
        kwargs={"directory": ts_dir},
        wait=True,
    )
    training_set_menu.add_option(
        "3", "Make Models", ModelTools.make_models_menu, kwargs={"directory": ts_dir},
    )
    training_set_menu.add_space()
    training_set_menu.add_option(
        "a", "Auto Run AIMAll", AutoTools.submit_aimall, kwargs={"directory": ts_dir},
    )
    training_set_menu.add_option("m", "Auto Make Models", AutoTools.run_models)
    training_set_menu.add_space()
    training_set_menu.add_final_options()

    # === Sample Set Menu ===#
    sample_pool_menu = Menu(title="Sample Pool Menu")
    sample_pool_menu.add_option(
        "1", "Submit GJFs to Gaussian", submit_gjfs, kwargs={"directory": sp_dir},
    )
    sample_pool_menu.add_option(
        "2", "Submit WFNs to AIMAll", submit_wfns, kwargs={"directory": sp_dir}
    )
    sample_pool_menu.add_space()
    sample_pool_menu.add_option(
        "a", "Auto Run AIMAll", AutoTools.submit_aimall, kwargs={"directory": sp_dir},
    )
    sample_pool_menu.add_final_options()

    # === Validation Set Menu ===#
    validation_set_menu = Menu(title="Validation Set Menu")
    validation_set_menu.add_option(
        "1", "Submit GJFs to Gaussian", submit_gjfs, kwargs={"directory": vs_dir},
    )
    validation_set_menu.add_option(
        "2", "Submit WFNs to AIMAll", submit_wfns, kwargs={"directory": vs_dir}
    )
    validation_set_menu.add_space()
    validation_set_menu.add_option(
        "a", "Auto Run AIMAll", AutoTools.submit_aimall, kwargs={"directory": vs_dir},
    )
    validation_set_menu.add_final_options()

    # === Properties Menu ===#
    properties_menu = Menu(
        title="Run Properties Menu",
        message="Perform adaptive sampling on a per-property basis",
    )
    properties_menu.add_option("r", "Auto Run Properties", PropertyTools.run, wait=True)
    properties_menu.add_option(
        "d",
        "Auto Run Properties as Background Process (recommended)",
        PropertyTools.run_daemon,
    )
    properties_menu.add_space()
    properties_menu.add_option(
        "l", "Collate All Models From Log", PropertyTools.collate_log
    )
    properties_menu.add_space()
    properties_menu.add_option(
        "c",
        "Check if Background Process Is Running",
        PropertyTools.check_daemon,
        wait=True,
    )
    properties_menu.add_option(
        "s",
        "Stop Execution of Background Process",
        PropertyTools.stop_daemon,
        wait=True,
    )
    properties_menu.add_final_options()

    # === Analysis Menu ===#
    analysis_menu = Menu(title="Analysis Menu")
    analysis_menu.add_option("dlpoly", "Test Models with DLPOLY", dlpoly_analysis)
    analysis_menu.add_option(
        "opt", "Perform Geometry Optimisation on First Point in Sample Pool", opt,
    )
    analysis_menu.add_option("s", "Create S-Curves", S_CurveTools.run)
    analysis_menu.add_option(
        "r", "Calculate Recovery Errors", RecoveryErrorTools.recovery_error_menu
    )
    analysis_menu.add_option(
        "rmse", "Calculate RMSE", RMSETools.rmse_menu
    )
    analysis_menu.add_final_options()

    # === Tools Menu ===#
    tools_menu = Menu(title="Tools Menu")
    tools_menu.add_option("setup", "Setup ICHOR Directories", SetupTools.directories)
    tools_menu.add_option("make", "Make Sets", SetupTools.make_sets)
    tools_menu.add_option("cp2k", "Setup CP2K run", CP2KTools.cp2k_menu)
    tools_menu.add_space()
    tools_menu.add_option("wfn", "Convert WFN to GJF", PointTools.wfn_to_gjf)
    tools_menu.add_option("csv", "Produce CSV From Set", SetTools.to_csv_menu)
    tools_menu.add_space()
    tools_menu.add_option("bak", "Revert All INT JSON Backup Files", Points.revert_backup)
    tools_menu.add_final_options()

    # === Options Menu ===#
    options_menu = Menu(title="Options Menu")
    options_menu.add_option(
        "settings", "Show and Change ICHOR Settings", SettingsTools.show
    )
    options_menu.add_option("ssh", "SSH into external machine", ssh)
    options_menu.add_final_options()

    # === Queue Menu ===#
    queue_menu = Menu(title="Queue Menu")
    queue_menu.add_option("stat", "Get qstat", BatchTools.qstat, wait=True)
    queue_menu.add_option("del", "Get qdel running jobs", BatchTools.qdel, wait=True)
    queue_menu.add_final_options()

    # === Main Menu ===#
    main_menu = Menu(
        title="ICHOR Main Menu",
        enable_problems=True,
        message=f"Running on {GLOBALS.MACHINE}",
        auto_clear=True,
    )
    main_menu.add_option("1", "Training Set", training_set_menu.run)
    main_menu.add_option("2", "Sample Pool", sample_pool_menu.run)
    main_menu.add_option("3", "Validation Set", validation_set_menu.run)
    main_menu.add_option(
        "4",
        "Calculate Errors",
        calculate_errors,
        kwargs={"models_directory": models_dir, "sample_pool_directory": sp_dir,},
    )
    main_menu.add_space()
    main_menu.add_option("r", "Auto Run", AutoTools.run)
    main_menu.add_option("p", "Run Properties", properties_menu.run)
    main_menu.add_space()
    main_menu.add_option("a", "Analysis", analysis_menu.run)
    main_menu.add_option("t", "Tools", tools_menu.run)
    main_menu.add_option("o", "Options", options_menu.run)
    main_menu.add_option("q", "Queue", queue_menu.run)

    main_menu.add_option(
        "dlpoly", "DLPOLY Analysis Options", dlpoly_analysis, hidden=True
    )

    main_menu.add_final_options(back=False)
    main_menu.run()


Arguments.read()
Globals.define()

if __name__ == "__main__":
    atexit.register(FileRemover.run_daemon)

    if Arguments.call_external_function is not None:
        Arguments.call_external_function(*Arguments.call_external_function_args)
        quit()

    main_menu()
