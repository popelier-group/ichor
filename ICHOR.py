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
  Version: 2.0
  Date: 30-09-2019

  ICHOR Design Principles:
  -- All within one script, this is up for debate however this script currently requires high portabilty and therefore
     is being designed within one script
  -- GLOBALS are in all caps and defined at the top of the script below the import statements
  -- Classes are defined next
  -- Functions are defined after Classes
  -- Main script is written beneath which calls functions when needed
  -- Main Menu is at the bottom, this should be easy to extend and is hopefully quite intuitive
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
import shutil
import hashlib
import logging
import platform
import warnings
import subprocess
from glob import glob
import itertools as it
from getpass import getpass
from functools import wraps
import multiprocessing as mp
from functools import lru_cache
from argparse import ArgumentParser

# Required imports
import numpy as np
from tqdm import tqdm
from numpy import linalg as la
from scipy.spatial import distance

#############################################
#                  Globals                  #
#############################################

DEFAULT_CONFIG_FILE = "config.properties"

CONFIG = None

SYSTEM_NAME = "SYSTEM"
ALF = []

AUTO_SUBMISSION_MODE = False
MAX_ITERATION = 1
POINTS_PER_ITERATION = 1

MULTIPLE_ADDITION_MODE = "manifold"

ITERATION = 0
STEP = 0

FORMAT_GJFS = True
METHOD = "B3LYP"
BASIS_SET = "6-31+g(d,p)"
KEYWORDS = []

ENCOMP = 3

BOAQ = "gs20"
IASMESH = "fine"

BOAQ_VALUES = ["auto", "gs1", "gs2", "gs3", "gs4", "gs5", "gs6", "gs7", "gs8",
               "gs9", "gs10", "gs15", "gs20", "gs25", "gs30", "gs35", "gs40", 
               "gs45", "gs50", "gs55", "gs60", "leb23", "leb25", "leb27", 
               "leb29", "leb31", "leb32"]

IASMESH_VALUES = ["sparse", "medium", "fine", "veryfine", "superfine"]

EXIT = False

FILE_STRUCTURE = []
IMPORTANT_FILES = {}

TRAINING_POINTS = []
SAMPLE_POINTS = []

TRAINING_POINTS_TO_USE = None

KERNEL = "rbf"                # only use rbf for now
FEREBUS_VERSION = "python"    # fortran (FEREBUS) or python (FEREBUS.py)
FEREBUS_LOCATION = "PROGRAMS/FEREBUS"

# CORE COUNT SETTINGS FOR RUNNING PROGRAMS (SUFFIX CORE_COUNT)
GAUSSIAN_CORE_COUNT = 2
AIMALL_CORE_COUNT = 2
FEREBUS_CORE_COUNT = 4
DLPOLY_CORE_COUNT = 1

# DLPOLY RUNTIME SETTINGS (PREFIX DLPOLY)
DLPOLY_NUMBER_OF_STEPS = 500    # Number of steps to run simulation for
DLPOLY_TEMPERATURE = 0        # If set to 0, will perform geom opt but default to 10 K
DLPOLY_PRINT_EVERY = 1        # Print trajectory and stats every n steps
DLPOLY_TIMESTEP = 0.001       # in ps
DLPOLY_LOCATION = "PROGRAMS/DLPOLY.Z"

MACHINE = ""
SGE = False
SUBMITTED = False

TRAINING_SET = None

NORMALIZE = False
PREDICTION_MODE = "george"    # ichor or george (recommend george)

PRECALCULATE_AIMALL = True

EXTERNAL_MACHINES = {
                        "csf3": "csf3.itservices.manchester.ac.uk",
                        "ffluxlab": "ffluxlab.mib.manchester.ac.uk"
                    }

SSH_SETTINGS = {
                "machine": "",
                "working_directory": "",
                "username": "",
                "password": ""
               }

#############################################
#:::::::::::::::::::::::::::::::::::::::::::#
#############################################

GAUSSIAN_METHODS = ['AM1', 'PM3', 'PM3MM', 'PM6', 'PDDG', 'PM7', 'HF', 
                    'CASSCF', 'MP2', 'MP3', 'MP4(SDQ)', 'MP4(SDQ,full)',
                    'MP4(SDTQ)', 'MP5', 'BD', 'CCD', 'CCSD', 'QCISD','BD(T)',
                    'CCSD(T)', 'QCISD(T)', 'BD(TQ)', 'CCSD(TQ)', 'QCISD(TQ)',
                    'EPT', 'CBS', 'GN', 'W1', 'CIS', 'TD', 'EOM', 'ZINDO',
                    'DFTB', 'CID', 'CISD', 'GVB', 'S', 'XA', 'B', 'PW91',
                    'mPW', 'G96', 'PBE', 'O', 'TPSS', 'BRx', 'PKZB', 'wPBEh',
                    'PBEh', 'VWN', 'VWN5', 'LYP', 'PL', 'P86', 'PW91', 'B95',
                    'PBE', 'TPSS', 'KCIS', 'BRC', 'PKZB', 'VP86', 'V5LYP',
                    'HFS', 'XAlpha', 'HFB', 'VSXC', 'HCTH', 'HCTH93', 
                    'HCTH147', 'HCTH407', 'tHCTH', 'M06L', 'B97D', 'B97D3',
                    'SOGGA11', 'M11L', 'N12', 'MN12L', 'B3LYP', 'B3P86',
                    'B3PW91', 'B1B95', 'mPW1PW91', 'mPW1LYP', 'mPW1PBE',
                    'mPW3PBE', 'B98', 'B971', 'B972', 'PBE1PBE', 'B1LYP',
                    'O3LYP', 'BHandH', 'BHandHLYP', 'BMK', 'M06', 'M06HF',
                    'M062X', 'tHCTHhyb', 'APFD', 'APF', 'SOGGA11X', 
                    'PBEh1PBE', 'TPSSh', 'X3LYP', 'HSEH1PBE', 'OHSE2PBE', 
                    'OHSE1PBE', 'wB97XD', 'wB97', 'wB97X', 'LC-wPBE',
                    'CAM-B3LYP', 'HISSbPBE', 'M11', 'N12SX', 'MN12SX', 'LC-']

AIMALL_FUNCTIONALS = ["MO62X", "B3LYP", "PBE"]

type2mass = {'H': 1.007825, 'He': 4.002603, 'Li': 7.016005, 'Be': 9.012182, 'B': 11.009305, 'C': 12.0,
             'N': 14.003074, 'O': 15.994915, 'F': 18.998403, 'Ne': 19.99244, 'Na': 22.989769, 'Mg': 23.985042,
             'Al': 26.981539, 'Si': 27.976927, 'P': 30.973762, 'S': 31.972071, 'Cl': 34.968853, 'Ar': 39.962383,
             'K': 38.963707, 'Ca': 39.962591, 'Sc': 44.955912, 'Ti': 47.947946, 'V': 50.94396, 'Cr': 51.940508,
             'Mn': 54.938045, 'Fe': 55.9349382, 'Co': 58.933195, 'Ni': 57.935343, 'Cu': 62.929598, 'Zn': 63.929142,
             'Ga': 68.925574, 'Ge': 73.921178, 'As': 74.921597, 'Se': 79.916521, 'Br': 78.918337, 'Kr': 83.911507}

type2rad = {'H': 0.37, 'He': 0.32, 'Li': 1.34, 'Be': 0.9, 'B': 0.82, 'C': 0.77, 'N': 0.74, 'O': 0.73, 'F': 0.71,
            'Ne': 0.69, 'Na': 1.54, 'Mg': 1.3, 'Al': 1.18, 'Si': 1.11, 'P': 1.06, 'S': 1.02, 'Cl': 0.99, 'Ar': 0.97,
            'K': 1.96, 'Ca': 1.74, 'Sc': 1.44, 'Ti': 1.36, 'V': 1.25, 'Cr': 1.27, 'Mn': 1.39, 'Fe': 1.25,
            'Co': 1.26, 'Ni': 1.21, 'Cu': 1.38, 'Zn': 1.31, 'Ga': 1.26, 'Ge': 1.22, 'As': 1.19, 'Se': 1.16,
            'Br': 1.14, 'Kr': 1.1}

dlpoly_weights =  {"H": 1.007975, "He": 4.002602, "Li": 6.9675, "Be": 9.0121831, "B": 10.8135, "C": 12.0106,
                   "N": 14.006855, "O": 15.9994, "F": 18.99840316, "Ne": 20.1797, "Na": 22.98976928, "Mg": 24.3055,
                   "Al": 26.9815385, "Si": 28.085, "P": 30.973762, "S": 32.0675, "Cl": 35.4515, "Ar": 39.948,
                   "K": 39.0983, "Ca": 40.078, "Sc": 44.955908, "Ti": 47.867, "V": 50.9415, "Cr": 51.9961,
                   "Mn": 54.938044, "Fe": 55.845, "Co": 58.933194, "Ni": 58.6934, "Cu": 63.546, "Zn": 65.38,
                   "Ga": 69.723, "Ge": 72.63, "As": 74.921595, "Se": 78.971, "Br": 79.904, "Kr": 83.798,
                   "Rb": 85.4678, "Sr": 87.62, "Y": 88.90584, "Zr": 91.224, "Nb": 92.90637, "Mo": 95.95}

#############################################
#:::::::::::::::::::::::::::::::::::::::::::#
#############################################

logging.basicConfig(filename='ichor.log',
                    level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s', 
                    datefmt='%d-%m-%Y %I:%M:%S')

_external_functions = {}

_call_external_function = None
_call_external_function_args = []

_IQA_MODELS = False

#############################################
#             Class Definitions             #
#############################################

class COLORS:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def format_blue(s):
        return COLORS.OKBLUE + s + COLORS.ENDC


class PATTERNS:
    COORDINATE_LINE = re.compile(r"\s*\w+(\s*[+-]?\d+.\d+([Ee]?[+-]?\d+)?){3}")

    AIMALL_LINE = re.compile(r"[<|]?\w+[|>]?\s+=(\s+[+-]?\d+.\d+([Ee]?[+-]?\d+)?)")
    MULTIPOLE_LINE = re.compile(r"Q\[\d+,\d+(,\w+)?]\s+=\s+[+-]?\d+.\d+([Ee]?[+-]?\d+)?")
    SCIENTIFIC = re.compile(r"[+-]?\d+.\d+([Ee]?[+-]?\d+)?")


class TabCompleter:
    def path_completer(self, text, state):
        try:
            import readline

            line = readline.get_line_buffer().split()
            if '~' in text:
                text = os.path.expanduser('~')
            if os.path.isdir(text):
                text += '/'
            return [x for x in glob(text + '*')][state]
        except ImportError:
            pass
    
    def create_list_completer(self, ll):
        def list_completer(text, state):
            try:
                import readline

                line   = readline.get_line_buffer()
                if not line:
                    return [c + " " for c in ll][state]
                else:
                    return [c + " " for c in ll if c.startswith(line)][state]
            except ImportError:
                pass

        self.list_completer = list_completer

    def setup_completer(self, completer):
        try:
            import readline

            readline.set_completer_delims("\t")
            readline.parse_and_bind("tab: complete")
            readline.set_completer(completer)
        except ImportError:
            pass


class Menu(object):
    def __init__(self, options=None, title=None, message=None, prompt=">>",
                 refresh=lambda *args: None, auto_clear=True, enable_problems=False, auto_close=False):
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
        options = []
        for label, option in self.options.items():
            if not label in self.gap_ids:
                if not label in self.message_ids:
                    if not label in self.hidden_options or include_hidden:
                        options.append(label)
        return options

    def add_option(self, label, name, handler, kwargs={}, wait=False, auto_close=False, hidden=False):
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
            max_len = UsefulTools.countDigits(len(problems))
            s = "s" if len(problems) > 1 else ""
            print(f"Problem{s} Found:")
            print()
            for i, problem in enumerate(problems):
                print(f"{i+1:{str(max_len)}d}) " +                # index problem
                      str(problem)                                # print problem
                      .replace("\n", "\n" + " " * (max_len + 2))) # fix indentation 
                print()

    def add_final_options(self, space=True, back=True, exit=True):
        self.add_space() if space else None
        self.add_option("b", "Go Back", Menu.CLOSE) if back else None
        self.add_option("0", "Exit", quit) if exit else None

    def longest_label(self):
        lengths = []
        for option in self.get_options(include_hidden=False):
            lengths += [len(option)]
        return max(lengths)

    # clear the screen
    # show the options
    def show(self):
        if self.auto_clear:
            os.system('cls' if os.name == 'nt' else 'clear')
        if self.problems_enabled:
            self.print_problems()
        if self.is_title_enabled:
            self.print_title()
        if self.is_message_enabled:
            print(self.message)
            print()
        label_width = self.longest_label()
        for label, option in self.options.items():
            if not label in self.gap_ids:
                if label in self.message_ids:
                    print(option[0].format(**option[1]))
                elif not label in self.hidden_options:
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
                return lambda: handler(**kwargs), index in self.wait_options, index in self.close_options
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

    global DEFAULT_CONFIG_FILE
    src = None
    prop = re.compile(r"([\w. ]+)\s*=\s*(.*)")

    def __init__(self, source=DEFAULT_CONFIG_FILE):
        self.src = source
        self.loadConfig()

    def loadConfig(self):
        if self.src.endswith(".properties"):
            self.loadPropertiesConfig()
        elif self.src.endswith(".yaml"):
            self.loadYamlConfig()

    def printKeyVals(self):
        for key in self:
            print("%s:\t%s" % (key, self[key]))

    def loadFileData(self):
        data = ""
        try:
            input = open(self.src, 'r')
            data = input.read()
            input.close()
        except IOError:
            pass

        return data

    def loadPropertiesConfig(self):
        for (key, val) in self.prop.findall(self.loadFileData()):
            self[self.cleanup_key(key)] = val

    def loadYamlConfig(self):
        import yaml
        entries = yaml.load(self.loadFileData())
        if entries:
            self.update(entries)

    def cleanup_key(self, key):
        return key.strip().replace(" ", "_").upper()

    def add_key_val(self, key, val):
        self[key] = val

    def write_key_vals(self):
        with open(self.src, "w+") as f:
            f.write(UsefulTools.ichor_logo)
            f.write("\n")
            for key in self:
                f.write("%s=%s\n" % (key, self[key]))


def sanitize_id(node_id):
    return node_id.strip().replace(" ", "")


(_ADD, _DELETE, _INSERT) = range(3)
(_ROOT, _DEPTH, _WIDTH) = range(3)


class Node:

    def __init__(self, name, identifier=None, expanded=True, is_file=False):
        self.__identifier = (str(uuid.uuid1()) if identifier is None else sanitize_id(str(identifier)))
        self.name = name
        self.expanded = expanded
        self.is_file = is_file
        self.__bpointer = None
        self.__fpointer = []

    @property
    def identifier(self):
        return self.__identifier

    @property
    def bpointer(self):
        return self.__bpointer

    @bpointer.setter
    def bpointer(self, value):
        if value is not None:
            self.__bpointer = sanitize_id(value)

    @property
    def fpointer(self):
        return self.__fpointer

    def update_fpointer(self, identifier, mode=_ADD):
        if mode is _ADD:
            self.__fpointer.append(sanitize_id(identifier))
        elif mode is _DELETE:
            self.__fpointer.remove(sanitize_id(identifier))
        elif mode is _INSERT:
            self.__fpointer = [sanitize_id(identifier)]


class Tree:

    def __init__(self):
        self.nodes = []

    def get_index(self, position):
        for index, node in enumerate(self.nodes):
            if node.identifier == position:
                break
        return index

    def create_node(self, name, identifier=None, parent=None, is_file=False):
        node = Node(name, identifier, is_file=is_file)
        self.nodes.append(node)
        self.__update_fpointer(parent, node.identifier, _ADD)
        node.bpointer = parent
        return node

    def show(self, position, level=_ROOT):
        queue = self[position].fpointer
        if level == _ROOT:
            print("{0} [{1}]".format(self[position].name, self[position].identifier))
        else:
            print("\t"*level, "{0} [{1}]".format(self[position].name, self[position].identifier))
        if self[position].expanded:
            level += 1
            for element in queue:
                self.show(element, level)  # recursive call

    def expand_tree(self, position, mode=_DEPTH):
        # Python generator. Loosly based on an algorithm from 'Essential LISP' by
        # John R. Anderson, Albert T. Corbett, and Brian J. Reiser, page 239-241
        yield position
        queue = self[position].fpointer
        while queue:
            yield queue[0]
            expansion = self[queue[0]].fpointer
            if mode is _DEPTH:
                queue = expansion + queue[1:]  # depth-first
            elif mode is _WIDTH:
                queue = queue[1:] + expansion  # width-first

    def is_branch(self, position):
        return self[position].fpointer

    def get_bpointer(self, position):
        return self[position].bpointer

    def get_file_path(self, position):
        file_path = [self[position].name]
        pos = position
        while self.get_bpointer(pos):
            file_path += [self[self.get_bpointer(pos)].name]
            pos = self.get_bpointer(pos)
        file_path = os.path.join(*list(reversed(file_path[:-1])), '')
        if self[position].is_file:
            file_path = file_path.rstrip(os.sep)
        return file_path

    def __update_fpointer(self, position, identifier, mode):
        if position is None:
            return
        else:
            self[position].update_fpointer(identifier, mode)

    def __update_bpointer(self, position, identifier):
        self[position].bpointer = identifier

    def __getitem__(self, key):
        return self.nodes[self.get_index(key)]

    def __setitem__(self, key, item):
        self.nodes[self.get_index(key)] = item

    def __len__(self):
        return len(self.nodes)

    def __contains__(self, identifier):
        return [node.identifier for node in self.nodes if node.identifier is identifier]


class FileTools:
    
    @staticmethod
    def clear_log(log_file="ichor.log"):
        with open(log_file, "w"): pass

    @staticmethod
    def setup_file_structure():
        tree = Tree()

        tree.create_node("ICHOR", "file_locs")

        tree.create_node("TRAINING_SET", "training_set", parent="file_locs")
        tree.create_node("SAMPLE_POOL", "sample_pool", parent="file_locs")
        tree.create_node("VALIDATION_SET", "validation_set", parent="file_locs")
        tree.create_node("FEREBUS", "ferebus", parent="file_locs")
        tree.create_node("MODELS", "models", parent="ferebus")
        tree.create_node("LOG", "log", parent="file_locs")
        tree.create_node("PROGRAMS", "programs", parent="file_locs")
        tree.create_node("OPT", "opt", parent="file_locs")
        tree.create_node("TEMP", "temp", parent="file_locs")

        tree.create_node("DLPOLY", "dlpoly", parent="file_locs")
        tree.create_node("GJF", "dlpoly_gjf", parent="dlpoly")

        tree.create_node("DATA", "data", parent="file_locs")
        tree.create_node("data", "data_file", parent="data", is_file=True)
        tree.create_node("JOBS", "jobs", parent="data")
        tree.create_node("ADAPTIVE_SAMPLING", "adaptive_sampling", parent="data")
        tree.create_node("alpha", "alpha", parent="adaptive_sampling", is_file=True)
        tree.create_node("cv_errors", "cv_errors", parent="adaptive_sampling", is_file=True)

        return tree

    @staticmethod
    def get_filetype(fname, return_dot=True):
        return os.path.splitext(fname)[1][int(not return_dot):]

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
            for f in l:
                if f.endswith(".gjf"): return True
            return False

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
        global FILE_STRUCTURE

        if file is None:
            file = "data_file"
        
        file = FILE_STRUCTURE.get_file_path(file)
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
                if not f is None:
                    return f
        return None

    @staticmethod
    def count_models(directory):
        n_models = 0
        for model_dir in FileTools.get_files_in(directory, "*/"):
            if len(FileTools.get_files_in(model_dir, "*_kriging_*.txt")) > 0:
                n_models += 1
        return n_models


class UsefulTools:

    @staticmethod
    @property
    def ichor_logo():
        ichor_encoded_string = ['"%s %s%s %s%s%s %s%s%s %s%s" % ("I"*10," "*8,"C"*13,"H"*9," "*5,"H"*9," "*5,"O"*9,'\
        '" "*5,"R"*17," "*3)',
        '"%s%s%s %s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s %s%s%s%s" % ("I",":"*8,"I"," "*5,"C"*3,":"*12,"C","H",":"*7,"H"'\
        '," "*5,"H",":"*7,"H"," "*3,"O"*2,":"*9,"O"*2," "*3,"R",":"*16,"R"," "*2)',
        '"%s%s%s %s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s %s%s%s%s%s%s" % ("I",":"*8,"I"," "*3,"C"*2,":"*15,"C","H",":"*7'\
        ',"H"," "*5,"H",":"*7,"H"," ","O"*2,":"*13,"O"*2," ","R",":"*6,"R"*6,":"*5,"R"," ")',
        '"%s%s%s %s%s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s %s%s%s%s%s%s%s" % ("I"*2,":"*6,"I"*2," "*2,"C",":"*5,"C"*8,'\
        '":"*4,"C","H"*2,":"*6,"H"," "*5,"H",":"*6,"H"*2,"O",":"*7,"O"*3,":"*7,"O","R"*2,":"*5,"R"," "*5,"R",'\
        '":"*5,"R")',
        '"%s%s%s%s%s %s%s%s%s%s%s %s%s%s%s%s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s%s%s%s" % (" "*2,"I",":"*4,"I"," "*2,'\
        '" ","C",":"*5,"C"," "*7,"C"*6," "*2,"H",":"*5,"H"," "*5,"H",":"*5,"H"," "*2,"O",":"*6,"O"," "*3,"O",":"*6,"O"'\
        '," "*2,"R",":"*4,"R"," "*5,"R",":"*5,"R")',
        '"%s%s%s%s%s %s%s%s%s %s%s%s%s%s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s%s%s%s" % (" "*2,"I",":"*4,"I"," "*2,"C",'\
        '":"*5,"C"," "*14," "*2,"H",":"*5,"H"," "*5,"H",":"*5,"H"," "*2,"O",":"*5,"O"," "*5,"O",":"*5,"O"," "*2,"R",'\
        '":"*4,"R"," "*5,"R",":"*5,"R")',
        '"%s%s%s%s%s %s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s%s%s" % (" "*2,"I",":"*4,"I"," "*2,"C",":"*5,'\
        '"C"," "*14," "*2,"H",":"*6,"H"*5,":"*6,"H"," "*2,"O",":"*5,"O"," "*5,"O",":"*5,"O"," "*2,"R",":"*4,"R"*6,'\
        '":"*5,"R"," ")',
        '"%s%s%s%s%s %s%s%s%s %s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s" % (" "*2,"I",":"*4,"I"," "*2,"C",":"*5,"C",'\
        '" "*14," "*2,"H",":"*17,"H"," "*2,"O",":"*5,"O"," "*5,"O",":"*5,"O"," "*2,"R",":"*13,"R"*2," "*2)',
        '"%s%s%s%s%s %s%s%s%s %s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s%s%s" % (" "*2,"I",":"*4,"I"," "*2,"C",":"*5,'\
        '"C"," "*14," "*2,"H",":"*17,"H"," "*2,"O",":"*5,"O"," "*5,"O",":"*5,"O"," "*2,"R",":"*4,"R"*6,":"*5,"R"," ")',
        '"%s%s%s%s%s %s%s%s%s %s%s%s%s%s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s%s%s%s" % (" "*2,"I",":"*4,"I"," "*2,"C",'\
        '":"*5,"C"," "*14," "*2,"H",":"*5,"H"," "*5,"H",":"*5,"H"," "*2,"O",":"*5,"O"," "*5,"O",":"*5,"O"," "*2,"R",'\
        '":"*4,"R"," "*5,"R",":"*5,"R")',
        '"%s%s%s%s%s %s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s%s%s%s" % (" "*2,"I",":"*4,"I"," "*2,"C",'\
        '":"*5,"C"," "*14," "*2,"H",":"*6,"H"*5,":"*6,"H"," "*2,"O",":"*5,"O"," "*5,"O",":"*5,"O"," "*2,"R",":"*4,"R",'\
        '" "*5,"R",":"*5,"R")',
        '"%s%s%s%s%s %s%s%s%s%s%s %s%s%s%s%s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s%s%s%s" % (" "*2,"I",":"*4,"I"," "*2,'\
        '" ","C",":"*5,"C"," "*7,"C"*6," "*2,"H",":"*5,"H"," "*5,"H",":"*5,"H"," "*2,"O",":"*6,"O"," "*3,"O",":"*6,"O"'\
        '," "*2,"R",":"*4,"R"," "*5,"R",":"*5,"R")',
        '"%s%s%s %s%s%s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s %s%s%s%s%s%s%s" % ("I"*2,":"*6,"I"*2," "*2,"C",":"*5,"C"*8,'\
        '":"*4,"C","H"*2,":"*6,"H"," "*5,"H",":"*6,"H"*2,"O",":"*7,"O"*3,":"*7,"O","R"*2,":"*5,"R"," "*5,"R",":"*5,'\
        '"R")',
        '"%s%s%s %s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s %s%s%s%s%s%s%s" % ("I",":"*8,"I"," "*3,"C"*2,":"*15,"C","H",'\
        '":"*7,"H"," "*5,"H",":"*7,"H"," ","O"*2,":"*13,"O"*2," ","R",":"*6,"R"," "*5,"R",":"*5,"R")',
        '"%s%s%s %s%s%s%s %s%s%s%s%s%s%s %s%s%s%s%s %s%s%s%s%s%s%s" % ("I",":"*8,"I"," "*5,"C"*3,":"*12,"C","H",'\
        '":"*7,"H"," "*5,"H",":"*7,"H"," "*3,"O"*2,":"*9,"O"*2," "*3,"R",":"*6,"R"," "*5,"R",":"*5,"R")',
        '"%s %s%s %s%s%s %s%s%s %s%s%s" % ("I"*10," "*8,"C"*13,"H"*9," "*5,"H"*9," "*5,"O"*9," "*5,"R"*8," "*5,'\
        '"R"*7)']

        ichor_string = ("{}\n"*23).format(
                         "#"*109,
                         "#%s#" % (":"*107),
                         "#::%s::#" % ("#"*103),
                         "#::#%s#::#" % (" "*101),
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
                         "#::#%s#::#" % (" "*101),
                         "#::%s::#" % ("#"*103),
                         "#%s#" % (":"*107),
                         "#"*109
                         )
        return ichor_string

    @staticmethod
    def nTrain():
        ts_dir = FILE_STRUCTURE.get_file_path("training_set")
        return FileTools.count_points_in(ts_dir)

    @staticmethod
    def natural_sort(l): 
        convert = lambda text: int(text) if text.isdigit() else text.lower() 
        alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
        return sorted(l, key = alphanum_key)

    @staticmethod
    def countDigits(n):
        import math
        return math.floor(math.log(n, 10)+1)

    @staticmethod
    def check_bool(val):
        return val.lower() in ['true', '1', 't', 'y', 'yes', 'yeah']

    @staticmethod
    def print_grid(arr, cols=10, color=None):
        import math
        ncols, _ = shutil.get_terminal_size(fallback=(80, 24))
        width = math.floor(ncols*0.9/cols)
        rows = math.ceil(len(arr)/cols)
        for i in range(rows):
            row = ""
            for j in range(cols):
                indx = cols*i+j
                if indx >= len(arr): break
                fname = arr[indx]
                string = f"{fname:{str(width)}s}"
                if fname == "scratch":
                    row += COLORS.OKGREEN + string + COLORS.ENDC
                else:
                    if color:
                        string = color + string + COLORS.ENDC
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
    def runFunc(order):
        def do_assignment(to_func):
            to_func.order = order
            return to_func
        return do_assignment
    
    @staticmethod
    def get_functions_to_run(obj):
        return sorted([getattr(obj, field) for field in dir(obj)
                        if hasattr(getattr(obj, field), "order")],
                        key = (lambda field: field.order))

    @staticmethod
    def externalFunc(*args):
        def run_func(func):
            global _external_functions
            if len(args) > 1:
                name = args[1]
            else:
                name = func.__name__
            _external_functions[name] = func
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
            return func # returning func means func can still be used normally
        return decorator

    @staticmethod
    def get_widths(line, ignore_chars=[]):
        pc = line[0]
        widths = [0]
        found_char = False
        for i, c in enumerate(line):
            if c != " ":
                found_char = True
            if pc == " " and c != " " and found_char and not c in ignore_chars:
                widths.append(i-1)
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


class my_tqdm:
    def __init__(self, iterator=None, *args, **kwargs):
        self.iterator = iterator
    
    def __next__(self):
        return next(self.iterator)
    
    def update(self):
        pass

    def set_description(self, desc=None):
        pass

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class FerebusTools:
    @staticmethod
    def write_finput(directory, natoms, atom, training_set_size, 
                       predictions=0, nproperties=1, optimization="pso"):
        global SYSTEM_NAME
        global KERNEL
        global FEREBUS_VERSION

        finput_fname = os.path.join(directory, "FINPUT.txt")
        atom_num = re.findall("\d+", atom)[0]

        line_break = "~" * 97

        with open(finput_fname, "w+") as finput:
            finput.write(f"{SYSTEM_NAME}\n")
            finput.write(f"natoms {natoms}\n")
            finput.write("starting_properties 1 \n")
            finput.write(f"nproperties {nproperties}\n")
            finput.write("#\n# Training set size and definition of reduced training set size\n#\n")
            finput.write(f"full_training_set {training_set_size}\n")
            finput.write("#\n# Prediction number and definition of new predictions\n#\n")
            finput.write(f"predictions {predictions}\n")
            if "py" in FEREBUS_VERSION:
                finput.write(f"kernel {KERNEL}\n")
            finput.write(
                "#\nfeatures_number 0        # if your are kriging only one atom or you don't want to use he standard "
                "calculation of the number of features based on DOF of your system. Leave 0 otherwise\n#\n")
            finput.write(f"#\n#{line_break}\n")

            finput.write("# Optimizers parameters\n#\n")
            finput.write("redo_weights n\n")
            finput.write("dynamical_selection n\n")
            finput.write(f"optimization {optimization}          "
                         "# choose between DE (Differential Evolution) "
                         "and PSO (Particle Swarm Optimization)\n")
            finput.write("fix P                    "
                         "# P = fixed p) T = fixed Theta (valid only for BFGS)) "
                         "N = nothing (i.e. optimization theta/p)\n")
            finput.write("p_value        2.00      # if no p optimization is used p_value MUST be inserted\n")
            finput.write("theta_max            1.0        "
                         "# select maximum value of theta for initialization "
                         "(Raise if receiving an error with Theta Values)\n")
            finput.write("theta_min            0.D0   # select maximum value of theta for initialization\n")
            finput.write("noise_specifier  n       "
                         "# answer yes (Y) to allow noise optimization, "
                         "no (N) to use no-noise option\n")
            finput.write("noise_value 0.1\n")
            finput.write("tolerance          1.0D-9 #\n")
            finput.write("convergence      200      #\n")
            finput.write("max_iterations   100000     #\n")
            finput.write(f"#\n#{line_break}\n")

            finput.write("# PSO Specific keywords\n#\n")
            finput.write("swarm_specifier  D       "
                         "# answer dynamic (D) or static "
                         "(S) as option for swarm optimization\n")
            finput.write("swarm_pop        1440       "
                         "# if swarm opt is set as 'static' the number of particle must be specified\n")
            finput.write("cognitive_learning   1.49400\n")
            finput.write("inertia_weight   0.72900\n")
            finput.write("social_learning   1.49400\n")
            finput.write(f"#\n#{line_break}\n")

            finput.write("# DE Specific keyword\n#\n")
            finput.write("population_size 8\n")
            finput.write("mutation_strategy 4\n")
            finput.write("population_reduction n\n")
            finput.write("reduction_start 5        # the ratio convergence/reduction_start < 5\n")
            finput.write(f"#\n#{line_break}\n")

            finput.write("# bfgs specific keywords\n#\n")
            finput.write("projg_tol 1.0d-2 # The iteration will stop when max{|proj g_i | i = 1, ...,n} <= projg_tol\n")
            finput.write("grad_tol 1.0d-7 # The iteration will stop when | proj g |/(1 + |f(x)|) <=grad_tol\n")
            finput.write("factor 1.0d+7 "
                         "# The iteration will stop when (f(x)^k -f(x)^{k+1})/max{|f(x)^k|,|f(x)^{k+1}|,1} "
                         "<= factor*epsmch\n")
            finput.write("#                     Typical values for factr: 1.d+12 for low accuracy) 1.d+7\n")
            finput.write("#                     for moderate accuracy) 1.d+1 for extremely high accuracy\n#\n")
            finput.write("iprint 101 # It controls the frequency and type of output generated:\n")
            finput.write("#                     iprint<0    no output is generated)\n")
            finput.write("#                     iprint=0    print only one line at the last iteration)\n")
            finput.write("#                     0<iprint<99 print also f and |proj g| every iprint iterations)\n")
            finput.write("#                     iprint=99   print details of every iteration except n-vectors)\n")
            finput.write("#                     iprint=100  print also the changes of active set and final x)\n")
            finput.write("#                     iprint>100  print details of every iteration including x and grad)\n")
            finput.write("#                     when iprint > 0 iterate.dat will be created\n")
            finput.write(f"#\n#{line_break}\n")

            finput.write("# Atoms type and index\n#\n")
            finput.write("atoms                      "
                         "# this keyword tells the program than the next lines are the index number and atom type\n")
            finput.write(f"{atom_num}   {atom}\n")


class Problem:
        def __init__(self, name="", problem="", solution=""):
            self.name = name
            self.problem = problem
            self.solution = solution
        
        def __str__(self):
            str_rep = f"Problem:     {self.name}\n" \
                      f"Description: {self.problem}\n" \
                      f"Solution:    {self.solution}"
            return str_rep
        
        def __repr__(self):
            return str(self)


class ProblemFinder:

    def __init__(self):
        self.problems = []

    @UsefulTools.runFunc(1)
    def check_alf(self):
        global ALF

        if len(ALF) < 1:
            self.add(Problem(name="ALF", 
                             problem="ALF not set due to error in calculation",
                             solution="Set 'ALF_REFERENCE_FILE' or manually set 'ALF' in config file"
                            ))
    
    @UsefulTools.runFunc(2)
    def check_directories(self):
        global FILE_STRUCTURE

        dirs_to_check = ["training_set", "sample_pool"]

        for dir_name in dirs_to_check:
            dir_path = FILE_STRUCTURE.get_file_path(dir_name)
            if not os.path.isdir(dir_path):
                self.add(Problem(name="Directory Not Found", 
                                 problem=f"Could not find: {dir_path}",
                                 solution="[S]etup directory structure or create manually"
                                ))

    def add(self, problem):
        self.problems.append(problem)

    def find(self):
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

#========================#
#     Cluster Tools      #
#========================#

class Job:
    def __init__(self, infile, flags=[], options={}, type=None, ncores=1, outfile=None, executable=""):
        self.infile = infile
        self.flags = flags
        self.options = options
        self.type = type

        self.outfile = self.get_outfile(outfile)

        self.setup = ""
        self.run_cmd = ""
        self.flags_string = ""
        self.options_string = ""
        self.output_string = ""
        self.finish = ""
        self.executable = executable

        self.infile_write = None
        self.outfile_write = None

        type_interface = {
                          "gaussian": self.gaussian_setup,
                          "ferebus": self.ferebus_setup,
                          "aimall": self.aimall_setup,
                          "python": self.python_setup,
                          "dlpoly": self.dlpoly_setup,
                          "dlpoly_gaussian": self.gaussian_setup,
                          "opt_gaussian": self.gaussian_setup,
                          None: self.generic_setup
                         }
        
        type_interface[self.type]()

    def get_outfile(self, outfile):
        if outfile is None:
            return os.path.splitext(self.infile)[0] + ".log"
        else:
            return outfile
    
    def _reset(self):
        self.options = {}
        self.flags = []
        self.setup = ""
        self.run_cmd = ""
        self.flags_string = ""
        self.options_string = ""
        self.output_string = ""
        self.finish = ""
        self.infile_write = None
        self.outfile_write = None

    def add_option(self, option, value=None):
        self.options[option] = value

    def gaussian_setup(self):
        global MACHINE
        self._reset()

        if "csf" in MACHINE.lower():
            self.setup = "export PREFERRED_SCDIR=~/scratch\n"
            self.run_cmd = "$g09root/g09/g09"
        elif "ffluxlab" in MACHINE.lower():
            self.run_cmd = "~/g09/rg09"
        else:
            self.run_cmd = "g09"

    def ferebus_setup(self):
        global FEREBUS_LOCATION
        global FEREBUS_VERSION
        global _IQA_MODELS
        self._reset()

        self.setup = f"pushd {self.infile}\n"
        self.finish = f"\npopd\npython {__file__} -f move_models {self.infile} {_IQA_MODELS}"
        if "py" in FEREBUS_VERSION.lower():
            self.run_cmd = "python "
        else:
            self.setup += "export OMP_NUM_THREADS=$NSLOTS"
            self.run_cmd = ""
        self.run_cmd += os.path.abspath(FEREBUS_LOCATION)
        if "py" in FEREBUS_VERSION.lower():
            self.run_cmd += ".py"
        self.infile_write = ""
        self.outfile_write = ""

    def aimall_setup(self):
        global BOAQ
        global ENCOMP
        global IASMESH
        global AIMALL_CORE_COUNT
        self._reset()

        self.run_cmd = "~/AIMAll/aimqb.ish"

        self.add_option("nogui")
        self.add_option("usetwoe", 0)
        self.add_option("atom", "all")
        self.add_option("encomp", ENCOMP)
        self.add_option("boaq", BOAQ)
        self.add_option("iasmesh", IASMESH)
        self.add_option("nproc", AIMALL_CORE_COUNT)

        self.output_string = "&>"

    def python_setup(self):
        # self._reset()
        self.run_cmd = f"python {self.infile}"
        self.output_string = self._setup_options()
        self.options = {}

        self.infile = ""
        self.outfile = ""
    
    def dlpoly_setup(self):
        global DLPOLY_LOCATION

        self._reset()
        self.setup = f"pushd {self.infile}\n"
        self.run_cmd = os.path.abspath(DLPOLY_LOCATION)
        self.finish = "\npopd"

        self.infile_write = ""
        self.outfile_write = ""

    def _setup_flags(self):
        flags = []
        for flag in self.flags:
            flag = str(flag)
            if not flag.startswith("-"):
                flag = "-" + flag
            flags.append(flag)
        return " ".join(flags)
    
    def _setup_options(self):
        options = []
        for option, value in self.options.items():
            option = str(option)
            if not option.startswith("-"):
                option = "-" + option
            if not value is None:
                if isinstance(value, list):
                    value = " ".join([str(val) for val in value])
                    options.append(f"{option} {value}")
                else:
                    value = str(value)
                    options.append(f"{option}={value}")
            else:
                options.append(f"{option}")
        return " ".join(options)

    def generic_setup(self):
        self.run_cmd = f"./{self.executable}"
        self.flags_string = self._setup_flags()
        self.options_string = self._setup_options()

    def check_parts(self):
        self.flags_string = self._setup_flags()
        self.options_string = self._setup_options()
        if self.setup:
            if not self.setup.endswith("\n"):
                self.setup += "\n"

        if self.infile_write is None:
            self.infile_write = self.infile
        if self.outfile_write is None:
            self.outfile_write = self.outfile

    @property
    def submit(self):
        self.check_parts()
        tokens = [
                  self.run_cmd, 
                  self.flags_string, 
                  self.options_string,
                  self.infile_write, 
                  self.output_string,
                  self.outfile_write,
                  self.finish
                 ]
        submission_string = self.setup
        for token in tokens:
            submission_string += token + " " if token else ""
        return submission_string
    
    @property
    def submit_sge(self):
        if self.type == "ferebus":
            self.infile, save_infile = "\"${inputs[$SGE_TASK_ID-1]}\"", self.infile
            self.ferebus_setup()
            self.infile = save_infile
        elif self.type == "dlpoly":
            self.infile, save_infile = "\"${inputs[$SGE_TASK_ID-1]}\"", self.infile
            self.dlpoly_setup()
            self.infile = save_infile

        self.infile_write = "\"${inputs[$SGE_TASK_ID-1]}\"" if self.infile else ""
        self.outfile_write = "\"${outputs[$SGE_TASK_ID-1]}\"" if self.outfile else ""
        return self.submit
    
    @property
    def data(self):
        return ",".join([self.infile, self.outfile])

    def __repr__(self):
        return self.submit


class SubmissionScript:
    def __init__(self, name="submit.sh", cores=1, type=None, label=None):
        self.fname = self.check_name(name)
        self.label = label
        self.type = type.lower()

        self.cores = cores
        self.options = {}
        self.modules = []
        self.jobs = []
        self.dir = None
        self.path = None
        self.sleep = 0

    def check_name(self, name):
        allowed_suffixes = ["sh", "sge"]
        if not "." in name or not name.split(".")[1] in allowed_suffixes:
            return name + ".sh"
        else:
            return name
    
    def load(self, module):
        if module not in self.modules:
            self.modules.append(module)

    def add_job(self, infile, flags=[], options={}, outfile=None, executable=""):
        self.jobs.append(Job(infile, flags, options, self.type, self.cores, outfile, executable))
    
    @property
    def njobs(self):
        return len(self.jobs)

    def check_options(self):
        options = {}
        for option, setting in self.options.items():
            if not option.startswith("-"):
                options["-" + option] = setting
        self.options = options
    
    def add_option(self, option, value=None):
        self.options[option] = value

    @property
    def queue(self):
        global MACHINE
        return Queues().get_queue(MACHINE.lower(), self.cores)

    def check_settings(self):
        self.check_options()
        if self.type is None:
            self.type = "generic"
            
    def write(self):
        global SGE
        global FILE_STRUCTURE

        self.check_settings()
        if len(self.jobs) == 0:
            return

        if SGE:
            data_directory = FILE_STRUCTURE.get_file_path("jobs")
            FileTools.mkdir(data_directory)
            data_file = os.path.join(data_directory, self.type)
            abs_data_file = os.path.abspath(data_file)

            logging.debug(f"Writitng to {data_file}")

            with open(data_file, "w") as f:
                for job in self.jobs:
                    f.write(f"{job.data}\n")

        with open(self.fname, "w") as f:
            # Settings / Flags
            f.write("#!/bin/bash -l\n")
            f.write("#$ -cwd\n")
            if self.label:
                f.write(f"#$ -N {self.label}")
            for option, setting in self.options.items():
                if setting:
                    f.write(f"#$ {option} {setting}\n")
                else:
                    f.write(f"#$ {option}\n")
            if self.cores > 1:
                if not self.queue:
                    f.write(f"#$ -pe {self.cores}\n")
                else:
                    f.write(f"#$ -pe {self.queue} {self.cores}\n")
            if self.njobs > 1 and SGE:
                f.write(f"#$ -t 1-{self.njobs}\n")
            else:
                f.write(f"#$ -t 1")
            f.write("\n")

            # Load Modules
            for module in self.modules:
                f.write(f"module load {module}\n")
            f.write("\n")

            if SGE:
                if not self.type in ["python"]:
                    f.write(f"file=\"{abs_data_file}\"\n")
                    f.write("\n")
                    f.write("inputs=()\n")
                    f.write("outputs=()\n")
                    f.write("\n")
                    f.write("while IFS=, read -r input output\n")
                    f.write("do\n")
                    f.write("    inputs+=(\"$input\")\n")
                    f.write("    outputs+=(\"$output\")\n")
                    f.write("done < \"$file\"\n")
                    f.write("\n")
                    f.write("if [ ${inputs[$SGE_TASK_ID-1]} ]\n")
                    f.write("then\n")
                f.write(f"    {self.jobs[0].submit_sge}\n")
                if not self.type in ["python"]:
                    f.write("fi\n")
            else:
                for job in self.jobs:
                    f.write(f"{job}\n")
        
    def submit(self, hold=None, return_jid=False):
        return BatchTools.qsub(self.fname, hold=hold, return_jid=return_jid)


class _Queue:
    def __init__(self, name="", low=1, high=1):
        self.name = name
        self.low = low
        self.high = high


class _Queues:
    def __init__(self, machine):
        self.machine = machine
        self._queues = []
    
    def add(self, queue):
        self._queues.append(queue)

    def add_queue(self, name="", low=1, high=1):
        self.add(_Queue(name, low, high))
    
    def get_queue(self, ncores):
        global DEFAULT_CONFIG_FILE

        for queue in self:
            if ncores >= queue.low and ncores <= queue.high:
                return queue.name

        print(f"Error: Cannot find queue on {self.machine} for {ncores} cores")
        print(f"Check {DEFAULT_CONFIG_FILE}")
        quit()
    
    def __getitem__(self, i):
        return self._queues[i]


class Queues:
    def __init__(self):
        self._queues = {}
        self.setup_queues()

    def setup_queues(self):
        queues_to_setup = UsefulTools.get_functions_to_run(self)
        for queue in queues_to_setup:
            machine = queue.__name__.split("_")[1]
            queue(machine)
    
    def create_queue(self, machine):
        return _Queues(machine)
    
    def add_queue(self, machine, queue):
        self._queues[machine] = queue

    @UsefulTools.runFunc(1)
    def setup_csf3_queues(self, machine):
        queue = self.create_queue(machine)
        queue.add_queue("smp.pe", 2, 32)
        self.add_queue(machine, queue)

    @UsefulTools.runFunc(2)
    def setup_ffluxlab_queues(self, machine):
        queue = self.create_queue(machine)
        queue.add_queue("smp", 2, 64)
        self.add_queue(machine, queue)
    
    @UsefulTools.runFunc(3)
    def setup_local_queues(self, machine):
        queue = self.create_queue(machine)
        queue.add_queue("", 1, mp.cpu_count())
        self.add_queue(machine, queue)

    def get_queue(self, machine, ncores):
        return self._queues[machine].get_queue(ncores)


class SubmissionTools:
    g09_modules = {
                   "csf3": ["apps/binapps/gaussian/g09d01_em64t"],
                   "ffluxlab": [],
                   "local": []
                  }
    
    aim_modules = {
                   "csf3": [],
                   "ffluxlab": [],
                   "local": []
                  }
    
    ferebus_modules = {
                       "csf3": {
                                "fortran": ["mpi/intel-17.0/openmpi/3.1.3", 
                                            "libs/intel/nag/fortran_mark26_intel", 
                                            "apps/anaconda3/5.2.0/bin"],
                                "python": ["apps/anaconda3/5.2.0/bin"]
                               },
                       "ffluxlab": {
                                    "fortran": ["mpi/intel/18.0.3",
                                                "libs/intel/nag/fortran_mark23_intel"],
                                    "python": []
                                   },
                       "local": {
                                 "fortran": [],
                                 "python": []
                                },
                      }
    
    python_modules = {
                      "csf3": ["apps/anaconda3/5.2.0/bin"],
                      "ffluxlab": [],
                      "local": []
                     }

    dlpoly_modules = {
                      "csf3": ["compilers/gcc/8.2.0"],
                      "ffluxlab": ["compilers/gcc/8.2.0"],
                      "local": []
                     }

    @staticmethod
    def make_g09_script(points, directory="", redo=False, submit=True, hold=None, return_jid=False, modify=None):
        global MACHINE
        global GAUSSIAN_CORE_COUNT

        name = os.path.join(directory, "GaussSub.sh")

        job_type = "gaussian"
        if modify:
            job_type = modify + "_" + job_type

        script = SubmissionScript(name=name, type=job_type, cores=GAUSSIAN_CORE_COUNT)
        for module in SubmissionTools.g09_modules[MACHINE.lower()]:
            script.load(module)
        
        if isinstance(points, Points):
            for point in points:
                if point.gjf and (redo or not os.path.exists(point.gjf.wfn_fname)):
                    script.add_job(point.gjf.fname)
        elif isinstance(points, GJF):
            if points and (redo or not os.path.exists(points.wfn_fname)):
                script.add_job(points.fname)

        script.write()
        if submit:
            jid = script.submit(hold=hold, return_jid=return_jid)
            if return_jid:
                return script.fname, jid
        return script.fname
    
    @staticmethod
    def make_aim_script(points, directory="", check_wfns=True, redo=False, submit=True, hold=None, return_jid=False):
        global MACHINE
        global AIMALL_CORE_COUNT

        if check_wfns:
            points.check_wfns()

        name = os.path.join(directory, "AIMSub.sh")
        script = SubmissionScript(name=name, type="aimall", cores=AIMALL_CORE_COUNT)

        script.add_option("j", "y")
        # script.add_option("o", "AIMALL.log")
        # script.add_option("e", "AIMALL.err")
        script.add_option("S", "/bin/bash")

        for module in SubmissionTools.aim_modules[MACHINE.lower()]:
            script.load(module)
        
        for point in points:
            if point.wfn and (redo or not point.wfn.aimall_complete):
                script.add_job(point.wfn.fname)
            elif point.gjf and not check_wfns:
                script.add_job(point.gjf.wfn_fname)
            
        script.write()
        if submit:
            jid = script.submit(hold=hold, return_jid=return_jid)
            if return_jid:
                return script.fname, jid
        return script.fname
    
    @staticmethod
    def make_ferebus_script(model_directories, directory="", submit=True, hold=None, return_jid=False):
        global MACHINE
        global FEREBUS_VERSION
        global FEREBUS_CORE_COUNT

        name = os.path.join(directory, "FereSub.sh")
        script = SubmissionScript(name=name, type="ferebus", cores=FEREBUS_CORE_COUNT)

        for module in SubmissionTools.ferebus_modules[MACHINE.lower()][FEREBUS_VERSION.lower()]:
            script.load(module)
        
        for model_directory in model_directories:
            script.add_job(model_directory)
            
        script.write()
        if submit:
            jid = script.submit(hold=hold, return_jid=return_jid)
            if return_jid:
                return script.fname, jid
        return script.fname
    
    @staticmethod
    def make_python_script(python_script, directory="", function="", args=(), submit=True, hold=None, return_jid=False):
        name = os.path.join(directory, "PySub.sh")
        script = SubmissionScript(name=name, type="python")

        for module in SubmissionTools.python_modules[MACHINE.lower()]:
            script.load(module)
        
        if function:
            script.add_job(python_script, options={"f": [function] + list(args)})
        else:
            script.add_job(python_script)

        script.write()
        if submit:
            jid = script.submit(hold=hold, return_jid=return_jid)
            if return_jid:
                return script.fname, jid
        return script.fname

    @staticmethod
    def make_dlpoly_script(dlpoly_directories, directory="", submit=True, hold=None, return_jid=False):
        global MACHINE
        global DLPOLY_CORE_COUNT

        name = os.path.join(directory, "DlpolySub.sh")
        script = SubmissionScript(name=name, type="dlpoly", cores=DLPOLY_CORE_COUNT)

        for module in SubmissionTools.dlpoly_modules[MACHINE.lower()]:
            script.load(module)

        for dlpoly_directory in dlpoly_directories:
            script.add_job(dlpoly_directory)
        
        script.write()
        if submit:
            jid = script.submit(hold=hold, return_jid=return_jid)
            if return_jid:
                return script.fname, jid
        return script.fname
        

class BatchTools:
    jid_fname = "jid"
    
    @staticmethod
    def _cleanup_jids(jid_file):
        with open(jid_file, "r") as f:
            data = f.readlines()
        running_jobs = BatchTools.qstat(quiet=True)
        keep_jobs = []
        for jid in data:
            if jid.strip() in running_jobs:
                keep_jobs.append(jid.strip())
        with open(jid_file, "w") as f:
            for jid in keep_jobs:
                f.write(f"{jid}\n")
    
    @staticmethod
    def run_cmd(cmd):
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode("ascii")

    @staticmethod
    def parse_tasks(job_line):
        tasks = []
        if "-" in job_line["ja-task-ID"]:
            task_ids = re.findall(r"\d+", job_line["ja-task-ID"])
            for _ in range(int(task_ids[0]), int(task_ids[1])+1):
                tasks.append(SGE_Task(job_line["state"], job_line["slots"]))
        else:
            tasks.append(SGE_Task(job_line["state"], job_line["slots"]))
        return tasks

    @staticmethod
    def qstat(quiet=False):
        output = BatchTools.run_cmd("qstat")
        headers, widths = [], []
        jobs = SGE_Jobs()
        job_line = {}
        job = SGE_Job("", "")
        for line in output.split("\n"):
            if line.startswith("-") or not line.strip(): continue
            if not headers:
                widths =  UsefulTools.get_widths(line, ignore_chars=["a"])
                headers = UsefulTools.split_widths(line, widths, strip=True)
            else:
                for header, column in zip(headers, UsefulTools.split_widths(line, widths)):
                    job_line[header] = column.strip()
                if not job_line["job-ID"] == job.jid:
                    if job:
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
    def qsub(script, hold=None, return_jid=False):
        global SGE
        global SUBMITTED
        global FILE_STRUCTURE

        data_dir = FILE_STRUCTURE.get_file_path("jobs")
        FileTools.mkdir(data_dir)
        jid_fname = os.path.join(data_dir, BatchTools.jid_fname)
        jid_file = open(jid_fname, "a")

        qsub_cmd = ""
        if SGE and not SUBMITTED:
            qsub_cmd = "qsub "
            if hold:
                if hold in BatchTools.qstat(quiet=True):
                    qsub_cmd += "-hold_jid " +  str(hold) + " "
        else:
            qsub_cmd = "bash "
        qsub_cmd += script
        qsub_cmd = [qsub_cmd]
        if not SUBMITTED:
            output = BatchTools.run_cmd(qsub_cmd)
            if SGE:
                jid = re.findall(r"\d+", output)
                if len(jid) > 0:
                    jid = jid[0]
                    jid_file.write(f"{jid}\n")
                    jid_file.close()
                    return jid if return_jid else None
        jid_file.close()

    @staticmethod
    def qdel():
        data_dir = FILE_STRUCTURE.get_file_path("jobs")
        jid_fname = os.path.join(data_dir, BatchTools.jid_fname)
        BatchTools._cleanup_jids(jid_fname)
        with open(jid_fname, "r") as f:
            for jid in f:
                jid = jid.strip()
                if jid in BatchTools.qstat(quiet=True):
                    BatchTools.run_cmd([f"qdel {jid}"])
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
              "EhRqw": "ERROR"
             }

    ## SGE QUEUE STATES ###########################################################################################
    # | Pending       | pending                                        | qw                  |                    #
    # | Pending       | pending, user hold                             | qw                  |                    #
    # | Pending       | pending, system hold                           | hqw                 |                    #
    # | Pending       | pending, user and system hold                  | hqw                 |                    #
    # | Pending       | pending, user hold, re-queue                   | hRwq                |                    #
    # | Pending       | pending, system hold, re-queue                 | hRwq                |                    #
    # | Pending       | pending, user and system hold, re-queue        | hRwq                |                    #
    # | Pending       | pending, user hold                             | qw                  |                    #
    # | Pending       | pending, user hold                             | qw                  |                    #
    # | Running       | running                                        | r                   |                    #
    # | Running       | transferring                                   | t                   |                    #
    # | Running       | running, re-submit                             | Rr                  |                    #
    # | Running       | transferring, re-submit                        | Rt                  |                    #
    # | Suspended     | obsuspended                                    | s,  ts              |                    #
    # | Suspended     | queue suspended                                | S, tS               |                    # 
    # | Suspended     | queue suspended by alarm                       | T, tT               |                    #
    # | Suspended     | allsuspended withre-submit                     | Rs,Rts,RS, RtS, RT, RtT |                #
    # | Error         | allpending states with error                   | Eqw, Ehqw, EhRqw        |                #
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
        for task in self:
            if task.is_running:
                return True
        return False   
    
    @property
    def is_holding(self):
        for task in self:
            if task.is_holding:
                return True
        return False  

    @property
    def is_waiting(self):
        for task in self:
            if task.is_waiting:
                return True
        return False   

    def __eq__(self, jid):
        print(self.jid, jid)
        return int(self.jid) == int(jid)

    def __len__(self):
        return len(self.tasks)

    def __getitem__(self, i):
        return self.tasks[i]
    
    def __bool__(self):
        return not self.tasks == []
    
    def __str__(self):
        s = f"Job: {self.name}, ID: {self.jid}, nTasks: {self.ntasks}\n"
        task_status = ""
        skip = True
        for i, task in enumerate(self):
            if task.status != task_status or i == len(self)-1:
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
        n_jobs = 0
        for job in self:
            if job.is_running:
                n_jobs += 1
        return n_jobs
    
    @property
    def n_holding(self):
        n_jobs = 0
        for job in self:
            if job.is_holding:
                n_jobs += 1
        return n_jobs
    
    @property
    def n_waiting(self):
        n_jobs = 0
        for job in self:
            if job.is_waiting:
                n_jobs += 1
        return n_jobs

    @property
    def jids(self):
        return [str(job.jid) for job in self]

    @property
    def names(self):
        return [str(job.name) for job in self]

    def __contains__(self, j):
        return  str(j) in self.jids or str(j) in self.names

    def __len__(self):
        return len(self.jobs)

    def __getitem__(self, i):
        return self.jobs[i]
    
    def __str__(self):
        s = f"Total Jobs: {self.njobs}\n--"
        for job in self:
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
        global FILE_STRUCTURE
        if not directory:
            directory = FILE_STRUCTURE.get_file_path("training_set")
        return AutoTools.submit_ichor("submit_gjfs", directory, submit=True, hold=jid, return_jid=True)

    @staticmethod
    def submit_ichor_wfns(jid=None, directory=None):
        global FILE_STRUCTURE
        if not directory:
            directory = FILE_STRUCTURE.get_file_path("training_set")
        return AutoTools.submit_ichor("submit_wfns", directory, submit=True, hold=jid, return_jid=True)

    @staticmethod
    def submit_ichor_models(jid=None):
        global FILE_STRUCTURE
        ts_dir = FILE_STRUCTURE.get_file_path("training_set")
        return AutoTools.submit_ichor("_make_models", ts_dir, "iqa", submit=True, hold=jid, return_jid=True)
    
    @staticmethod
    def submit_ichor_errors(jid=None):
        global FILE_STRUCTURE
        sp_dir = FILE_STRUCTURE.get_file_path("sample_pool")
        model_dir = FILE_STRUCTURE.get_file_path("models")
        return AutoTools.submit_ichor("calculate_errors", model_dir, sp_dir, submit=True, hold=jid, return_jid=True)

    @staticmethod
    def submit_dlpoly_gjfs(jid=None):
        global FILE_STRUCTURE
        return AutoTools.submit_ichor("calculate_gaussian_energies", submit=True, hold=jid, return_jid=True)

    @staticmethod
    def submit_dlpoly_energies(jid=None):
        global FILE_STRUCTURE
        return AutoTools.submit_ichor("get_wfn_energies", submit=True, hold=jid, return_jid=True)

    @staticmethod
    def submit_ichor(function, *args, submit=False, hold=None, return_jid=False):
        return SubmissionTools.make_python_script(__file__, function=function, args=args, submit=submit, hold=hold, return_jid=return_jid)

    @staticmethod
    def submit_gjfs(jid=None, npoints=None, modify=None):
        global POINTS_PER_ITERATION
        if npoints is None:
            npoints = POINTS_PER_ITERATION
        points = Points()
        points.make_gjf_template(npoints)
        return points.submit_gjfs(redo=False, submit=True, hold=jid, return_jid=True, modify=modify)

    @staticmethod
    def submit_wfns(jid=None, npoints=None):
        global POINTS_PER_ITERATION
        if npoints is None:
            npoints = POINTS_PER_ITERATION
        points = Points()
        points.make_wfn_template(npoints)
        return points.submit_wfns(redo=False, submit=True, hold=jid, return_jid=True)

    @staticmethod
    def submit_models(jid=None):
        ts_dir = FILE_STRUCTURE.get_file_path("training_set")
        gjf = Points(ts_dir, read_gjfs=True, first=True)[0]
        return SubmissionTools.make_ferebus_script(gjf.atoms.atoms, submit=True, hold=jid, return_jid=True)

    @staticmethod
    def submit_aimall(directory=None, jid=None):
        npoints = FileTools.count_points_in(directory)

        script, jid = AutoTools.submit_ichor_gjfs(jid, directory=directory)
        script, jid = AutoTools.submit_gjfs(jid, npoints)
        script, jid = AutoTools.submit_ichor_wfns(jid, directory=directory)
        AutoTools.submit_wfns(jid, npoints)

#========================#
#      Point Tools       #
#========================#

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

    def read_input(self, coordinate_line):
        find_atom = coordinate_line.split()
        self.atom_type = find_atom[0]
        coordinate_line = next(re.finditer(r"(\s*[+-]?\d+.\d+([Ee][+-]?\d+)?){3}", coordinate_line)).group()
        coordinate_line = re.finditer(r"[+-]?\d+.\d+([Ee][+-]?\d+)?", coordinate_line)
        self.x = float(next(coordinate_line).group())
        self.y = float(next(coordinate_line).group())
        self.z = float(next(coordinate_line).group())

    def dist(self, other):
        dist = 0
        for icoord, jcoord in zip(self.coordinates, other.coordinates):
            dist += (icoord - jcoord)**2
        return np.sqrt(dist)

    def xdiff(self, other):
        return other.x - self.x
    
    def ydiff(self, other):
        return other.y - self.y

    def zdiff(self, other):
        return other.z - self.z

    def angle(self, atom1, atom2):
        temp = self.xdiff(atom1) * self.xdiff(atom2) + \
                self.ydiff(atom1) * self.ydiff(atom2) + \
                self.zdiff(atom1) * self.zdiff(atom2)
        return math.acos((temp / (self.dist(atom1) * self.dist(atom2))))

    def set_bond(self, jatom):
        if not jatom in self._bonds:
            self._bonds.append(jatom)

    def get_priorty(self, level):
        atoms = Atoms(self)
        for _ in range(level):
            atoms_to_add = []
            for atom in atoms:
                for bonded_atom in atom.bonds:
                    if not bonded_atom in atoms:
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
        return [self.xdiff(self.x_axis) / self.dist(self.x_axis),
                self.ydiff(self.x_axis) / self.dist(self.x_axis),
                self.zdiff(self.x_axis) / self.dist(self.x_axis)]

    def C_2k(self):
        xdiff1 = self.xdiff(self.x_axis)
        ydiff1 = self.ydiff(self.x_axis)
        zdiff1 = self.zdiff(self.x_axis)

        xdiff2 = self.xdiff(self.xy_plane)
        ydiff2 = self.ydiff(self.xy_plane)
        zdiff2 = self.zdiff(self.xy_plane)

        sigma_fflux = -(xdiff1 * xdiff2 + ydiff1 * ydiff2 + zdiff1 * zdiff2) / (
                xdiff1 * xdiff1 + ydiff1 * ydiff1 + zdiff1 * zdiff1)

        y_vec1 = sigma_fflux * xdiff1 + xdiff2
        y_vec2 = sigma_fflux * ydiff1 + ydiff2
        y_vec3 = sigma_fflux * zdiff1 + zdiff2

        yy = math.sqrt(y_vec1 * y_vec1 + y_vec2 * y_vec2 + y_vec3 * y_vec3)

        y_vec1 /= yy
        y_vec2 /= yy
        y_vec3 /= yy

        return [y_vec1, y_vec2, y_vec3]

    def C_3k(self, C_1k, C_2k):
        xx3 = C_1k[1]*C_2k[2] - C_1k[2]*C_2k[1]
        yy3 = C_1k[2]*C_2k[0] - C_1k[0]*C_2k[2]
        zz3 = C_1k[0]*C_2k[1] - C_1k[1]*C_2k[0]

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
        global type2mass
        return type2mass[self.atom_type]
    
    @property
    def radius(self):
        global type2rad
        return type2rad[self.atom_type]

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
        if not self.x_axis is None: alf.append(self.x_axis)
        if not self.xy_plane is None: alf.append(self.xy_plane)
        return alf

    @property
    def alf_nums(self):
        return [atom.num for atom in self.alf]

    def __str__(self):
        return f"{self.atom_type:<3s}{self.coordinates_string}"
    
    def __repr__(self):
        return str(self)
    
    def __eq__(self, other):
        return self.atom_num == other.atom_num

    def __hash__(self):
        return hash(str(self.num) + str(self.coordinates_string))


class Atoms:
    ALF = []

    def __init__(self, atoms=None):
        self._atoms = []
        self._connectivity = None

        if not atoms is None:
            self.add(atoms)

    def add(self, atom):
        if isinstance(atom, str):
            self._atoms.append(Atom(atom))
        elif isinstance(atom, Atom):
            self._atoms.append(atom)
        elif isinstance(atom, (list, Atoms)):
            for a in atom:
                self.add(a)
    
    def finish(self):
        Atom.counter = it.count(1)

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

    def __len__(self):
        return len(self._atoms)

    def __delitem__(self, i):
        del self._atoms[i]

    def __getitem__(self, i):
        return self._atoms[i]
    
    @property
    def masses(self):
        return [atom.mass for atom in self]

    @property
    def atoms(self):
        return [atom.atom_num for atom in self]

    @property
    def empty(self):
        return len(self) == 0

    def connect(self, iatom, jatom):
        iatom.set_bond(jatom)
        jatom.set_bond(iatom)

    @property
    @lru_cache()
    def connectivity(self):
        connectivity = np.zeros((len(self), len(self)))
        for i, iatom in enumerate(self):
            for j, jatom in enumerate(self):
                if not iatom == jatom:
                    max_dist = 1.2 * (iatom.radius + jatom.radius)

                    if iatom.dist(jatom) < max_dist:
                        connectivity[i][j] = 1
                        self.connect(iatom, jatom)

        return connectivity

    def to_angstroms(self):
        for atom in self:
            atom.to_angstroms()

    def to_bohr(self):
        for atom in self:
            atom.to_bohr()

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
    
    @property
    def alf(self):
        return [[iatom.num for iatom in atom.alf] for atom in self]

    def calculate_alf(self):
        self.connectivity
        for iatom in self:
            for alf_axis in range(2):
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
            atom.x_axis = self[atom_alf[1]-1]
            atom.xy_plane = self[atom_alf[2]-1]

    def calculate_features(self):
        if not Atoms.ALF:
            self.calculate_alf()
        self.set_alf()
        for atom in self:
            atom.calculate_features(self)
    
    @property
    def features(self):
        try:
            return self._features
        except AttributeError:
            self.calculate_features()
            self._features = [atom.features for atom in self]
            return self._features


class Point:
    counter = it.count(1)

    def __init__(self, directory="", gjf_fname="", wfn_fname="", int_directory="", int_fnames=[], 
                    read_gjf=False, read_wfn=False, read_ints=False):
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

    @property
    def atoms(self):
        return self.gjf._atoms

    @property
    def features(self):
        return self.atoms.features
    
    def get_directory(self):
        return self.directory

    def get_true_value(self, value_to_get, atoms=False):
        if value_to_get == "iqa":
            eiqa = 0 if not atoms else [0]*len(self.atoms)
            for int_atom, int_data in self.ints.items():
                if not atoms:
                    eiqa += int_data.eiqa
                else:
                    eiqa[int_data.num - 1] = int_data.eiqa
            return eiqa

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
            global SYSTEM_NAME
            self.point_num = 1
            self.system_name = SYSTEM_NAME

    def __get_features(self):
        training_set = {}
        self.atoms.features
        for atom in self.atoms:
            training_set[atom.atom_num] = {"features": atom.features}
        return training_set

    def training_set_lines(self, model_type):
        model_types = {"iqa": self.iqa_training_set_line, 
                       "multipoles": self.multipole_training_set_line}
        
        delimiter = " "
        number_of_outputs = 25

        point_data = model_types[model_type]()
        point_lines = {}
        nproperties = 0
        for atom, data in point_data.items():
            features = delimiter.join([str(feature) for feature in data["features"]])
            nproperties = len(data["outputs"])
            outputs = UsefulTools.format_list(data["outputs"], number_of_outputs)
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
            training_set[atom]["outputs"] = list(self.ints[atom].multipoles.values())
        return training_set

    def move(self, new_directory):
        FileTools.mkdir(new_directory)

        self.gjf.move(new_directory)
        self.wfn.move(new_directory)
        for int_file in self.int_fnames:
            int_file.move(new_directory)

        self.directory = new_directory


class GJF(Point):
    jobs = {
            "energy": "p",
            "opt": "opt",
            "freq": "freq"
           }

    def __init__(self, fname="", read=False):
        self.fname = fname
        self._atoms = Atoms()

        self.job_type = "energy"   # energy/opt/freq
        self.method = "b3lyp"
        self.basis_set = "6-31+g(d,p)"

        self.charge = 0
        self.multiplicity = 1

        self.header_line = ""

        self.title = FileTools.get_basename(self.fname, return_extension=False)
        self.wfn_fname = ""

        self.startup_options = []
        self.keywords = []

        self.split_fname()

        if self.fname and read:
            self.read()

    def read(self):
        with open(self.fname, "r") as f:
            for line in f:
                if line .startswith("%"):
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
                if re.match(PATTERNS.COORDINATE_LINE, line):
                    self._atoms.add(line.strip())
                if line.endswith(".wfn"):
                    self._atoms.finish()
                    self.wfn_fname = line.strip()
    
    @property
    def job(self):
        return GJF.jobs[self.job_type]

    def format(self):
        global METHOD
        global KEYWORDS
        global BASIS_SET
        global GAUSSIAN_METHODS
        global GAUSSIAN_CORE_COUNT
        global DEFAULT_CONFIG_FILE

        if UsefulTools.in_sensitive(METHOD, GAUSSIAN_METHODS):
            self.method = METHOD
        else:
            print("Error: Unknown method {METHOD}")
            print("Check method in {DEFAULT_CONFIG_FILE}")
            quit()
        
        self.basis_set = BASIS_SET

        required_keywords = ["nosymm", "output=wfn"]
        self.keywords = list(set(self.keywords + KEYWORDS + required_keywords))

        self.startup_options = [
                                f"nproc={GAUSSIAN_CORE_COUNT}",
                                f"mem=1GB"
                                ]

        self.header_line = f"#{self.job} {self.method}/{self.basis_set} {UsefulTools.unpack(self.keywords)}\n"
        self.wfn_fname = self.fname.replace(".gjf", ".wfn")

    def move(self, directory):
        if self:
            if directory.endswith(os.sep):
                directory = directory.rstrip(os.sep)
            point_name = os.path.basename(directory)
            new_name = os.path.join(directory, point_name + ".gjf")
            FileTools.move_file(self.fname, new_name)
            self.fname = new_name

    def write(self):
        self.format()
        with open(self.fname, "w") as f:
            for startup_option in self.startup_options:
                f.write(f"%" + startup_option + "\n")
            f.write(f"{self.header_line}\n")
            f.write(f"{self.title}\n\n")
            f.write(f"{self.charge} {self.multiplicity}\n")
            for atom in self._atoms:
                f.write(f"{str(atom)}\n")
            f.write(f"\n{self.wfn_fname}")
        
    def submit(self, modify=None):
        SubmissionTools.make_g09_script(self, redo=True, submit=True, modify=modify)

    def __len__(self):
        return len(self._atoms)
    
    def __getitem__(self, i):
        return self._atoms[i]

    def __bool__(self):
        return not self.fname == ""


class WFN(Point):
    global METHOD

    def __init__(self, fname="", read=False):
        self.fname = fname
        self.split_fname()

        self.title = ""
        self.header = ""

        self.mol_orbitals = 0
        self.primitives = 0
        self.nuclei = 0
        self.method = "HF"

        self._atoms = Atoms()

        self.energy = 0
        self.virial = 0

        self.split_fname()

        if read and self.fname:
            self.read()

    def read(self, only_header=False):
        if not os.path.exists(self.fname):
            return
        with open(self.fname, "r") as f:
            self.title = next(f)
            self.header = next(f)
            self.read_header()
            if only_header:
                return
            for line in f:
                if "CHARGE" in line:
                    self._atoms.add(line)
                if "CENTRE ASSIGNMENTS" in line:
                    self._atoms.finish
                if "TOTAL ENERGY" in line:
                    self.energy = line.split()[3]
                    self.virial = line.split()[-1]

    def read_header(self):
        global METHOD

        data = re.findall(r"\s\d+\s", self.header)

        self.mol_orbitals = int(data[0])
        self.primitives = int(data[1])
        self.nuclei = int(data[2])

        split_header = self.header.split()
        if split_header[-1] != "NUCLEI":
            self.method = split_header[-1]
        else:
            self.method = METHOD

    @property
    def aimall_complete(self):
        if not self.title:
            if os.path.exists(self.fname):
                self.read()
            else:
                return False
        aim_directory = self.title.strip() + "_atomicfiles"
        aim_directory = os.path.join(self.dirname, aim_directory)
        if not os.path.exists(aim_directory):
            return False
        n_ints = 0
        for f in os.listdir(aim_directory):
            if f.endswith(".int"):
                n_ints += 1
        if n_ints != self.nuclei:
            return False

        return True

    def __bool__(self):
        return not self.fname == ""

    def move(self, directory):
        if self:
            if directory.endswith(os.sep):
                directory = directory.rstrip(os.sep)
            point_name = os.path.basename(directory)
            new_name = os.path.join(directory, point_name + ".wfn")
            FileTools.move_file(self.fname, new_name)
            self.fname = new_name

    def check_functional(self):
        data = []
        with open(self.fname, "r") as f:
            for i, line in enumerate(f):
                if i == 1:
                    if not METHOD.upper() in line.upper():
                        f.seek(0)
                        data = f.readlines()
                    break
        
        if data != []:
            data[1] = data[1].strip() +  "   " + METHOD + "\n"
            with open(self.fname, "w") as f:
                f.writelines(data)
                

class INT(Point):
    def __init__(self, fname="", read=False):
        self.fname = fname
        self.atom = os.path.splitext(os.path.basename(self.fname))[0].upper()

        self.integration_results = {}
        self.multipoles = {}
        self.iqa_data = {}

        self.split_fname()

        if self.fname and read:
            self.read()
    
    @property
    def num(self):
        return int(re.findall("\d+", self.atom)[0])

    @property
    def integration_error(self):
        return self.integration_results["L"]

    @property
    def eiqa(self):
        return self.iqa_data["E_IQA(A)"]

    def move(self, directory):
        if self:
            if directory.endswith(os.sep):
                directory = directory.rstrip(os.sep)
            point_name = os.path.basename(directory)
            int_directory = point_name + "_atomicfiles"
            FileTools.mkdir(int_directory)
            new_name = os.path.join(directory, int_directory, self.atom.lower() + ".int")
            FileTools.move_file(self.fname, new_name)
            self.fname = new_name

    def read(self):
        with open(self.fname, "r") as f:
            for line in f:
                if "Results of the basin integration:" in line:
                    line = next(f)
                    while line.strip():
                        for match in re.finditer(PATTERNS.AIMALL_LINE, line):
                            tokens = match.group().split("=")
                            try:
                                self.integration_results[tokens[0].strip()] = float(tokens[-1])
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
                                multipole = tokens[0].strip().replace("[", "").replace(",", "").replace("]", "")
                                self.multipoles[multipole.lower()] = float(tokens[-1])
                            except ValueError:
                                print(f"Cannot convert {tokens[-1]} to float")
                        line = next(f)
                if "IQA Energy Components (see \"2EDM Note\"):" in line:
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

    
    def __bool__(self):
        return not self.fname == ""


class Model:
    def __init__(self, fname, read_model=False):
        self.fname = fname

        self.directory = ""
        self.basename = ""

        self.system_name = ""
        self.model_type = ""
        self.atom_number = ""

        self.analyse_name()

        self.nTrain = 0
        self.nFeats = 0

        self.mu = 0
        self.sigma2 = 0

        self.hyper_parameters = []
        self.weights = []

        self.y = []
        self.X = []
        if read_model and self.fname:
            self.read()

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
                    while not ";" in line:
                        self.hyper_parameters.append(float(line))
                        line = next(f)
                    self.hyper_parameters = np.array(self.hyper_parameters)
                if "Weights" in line:
                    line = next(f)
                    while not ";" in line:
                        self.weights.append(float(line))
                        line = next(f)
                    self.weights = np.array(self.weights)
                if "Property_value_Kriging_centers" in line:
                    line = next(f)
                    while not "training_data" in line:
                        self.y.append(float(line))
                        line = next(f)
                    self.y = np.array(self.y).reshape((-1, 1))
                if "training_data" in line:
                    line = next(f)
                    while not ";" in line:
                        self.X.append([float(num) for num in line.split()])
                        line = next(f)
                    self.X = np.array(self.X).reshape((self.nTrain, self.nFeats))

                if not up_to is None and up_to in line:
                    break

    def analyse_name(self):
        self.directory = os.path.dirname(self.fname)
        self.basename = os.path.basename(self.fname)

        fname_split = os.path.splitext(self.basename)[0].split("_")
        self.system_name = fname_split[0]
        self.model_type = fname_split[2].lower()
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
                if i > 10: break
        if data and no_noise_line > 0:
            del data[no_noise_line]
            with open(self.fname, "w") as f:
                f.writelines(data)

    def get_fname(self, directory=None):
        if directory is None:
            directory = self.directory
        basename = f"{self.system_name}_kriging_{self.model_type}_{self.atom_number}.txt"
        return os.path.join(directory, basename)
    
    def copy_to_log(self):
        log_directory = FILE_STRUCTURE.get_file_path("log")
        FileTools.mkdir(log_directory)

        if self.nTrain == 0:
            self.read(up_to="Number_of_training_points")

        nTrain = str(self.nTrain).zfill(4)
        log_directory = log_directory + f"{self.system_name}{nTrain}"
        FileTools.mkdir(log_directory)
        log_model_file = self.get_fname(log_directory)

        FileTools.copy_file(self.fname, log_model_file)

    def k(self, xi, xj):
        result = 0
        for i, j, h in zip(xi, xj, self.hyper_parameters):
            result += h * (i - j)**2
        return np.exp(-result)

    def r(self, features):
        r = np.empty((self.nTrain, 1))
        for i, point in enumerate(self.X):
            r[i] = self.k(features, point)
        return r

    @property
    def R(self):
        try:
            return self._R
        except AttributeError:
            self._R = np.empty((self.nTrain, self.nTrain))
            for i, xi in enumerate(self.X):
                for j, xj in enumerate(self.X):
                    self._R[i][j] = self.k(xi, xj)
            return self._R

    @property
    def invR(self):
        try:
            return self._invR
        except AttributeError:
            self._invR = la.inv(self.R)
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
            self._H = np.matmul(self.ones, 
                                la.inv(np.matmul(self.ones.T, 
                                                 self.ones)).item() * 
                                self.ones.T)
            return self._H

    @property
    def B(self):
        try:
            return self._B
        except AttributeError:
            self._B = np.matmul((la.inv(np.matmul(np.matmul(self.ones.T, self.invR), self.ones))),
                        np.matmul(np.matmul(self.ones.T, self.invR), self.y)).item()
            return self._B

    @property
    def cross_validation(self):
        try:
            return self._cross_validation
        except AttributeError:
            d = self.y - self.B * self.ones

            self._cross_validation = []
            for i in range(self.nTrain):
                cve = np.matmul(self.invR[i, :], (d + (d[i]/self.H[i][i]) * self.H[:][i].reshape((-1, 1)))) / self.invR[i][i]
                self._cross_validation.append(cve.item()**2)
            return self._cross_validation

    def predict(self, point):
        r = self.r(point.features[self.i])
        weights = self.weights.reshape((-1, 1))
        return self.mu + np.matmul(r.T, weights).item()
    
    def variance(self, point):
        r = self.r(point.features[self.i])

        res1 = np.matmul(r.T, np.matmul(self.invR, r))
        res2 = np.matmul(self.ones.T, np.matmul(self.invR, r))
        res3 = np.matmul(self.ones.T, np.matmul(self.invR, self.ones))

        s2 = self.sigma2 * (1 - res1.item() + (1 + res2.item())**2/res3.item())
        return s2
    
    def closest_point(self, point):
        point = np.array(point.features[self.i]).reshape((1, -1))
        return distance.cdist(point, self.X).argmin()

    def cross_validation_error(self, point):
        return self.cross_validation[self.closest_point(point)]

    def link(self, dst_dir):
        abs_path = os.path.abspath(self.fname)
        dst = os.path.join(dst_dir, self.basename)
        if os.path.exists(dst):
            os.remove(dst)
        os.symlink(abs_path, dst)


class Models:
    def __init__(self, directory, read_models=False):
        self._models = []
        self.directory = directory
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
        [model for model in self if model.model_type == type or type == "all"]

    def read(self):
        for model in self:
            model.read()

    def read_first(self):
        self[0].read()

    def add(self, model_file, read_model=False):
        self._models.append(Model(model_file, read_model=read_model))
    
    @lru_cache()
    def predict(self, points, atoms=False, type="iqa"):
        predictions = []
        for point in points:
            prediction = 0 if not atoms else [0]*len(self)
            for model in self.get(type):
                if not atoms:
                    prediction += model.predict(point) 
                else:
                    prediction[model.num - 1] = model.predict(point)
            predictions.append(prediction)
        return np.array(predictions) if not atoms else predictions
    
    @lru_cache()
    def variance(self, points):
        variances = []
        for point in points:
            variance = 0
            for model in self:
                variance += model.variance(point)
            variances.append(variance)
        return np.array(variances)
    
    @lru_cache()
    def cross_validation(self, points):
        cross_validation_errors = []
        for point in points:
            cross_validation_error = 0
            for model in self:
                cross_validation_error += model.cross_validation_error(point)
            cross_validation_errors.append(cross_validation_error)
        return np.array(cross_validation_errors)
    
    def calc_alpha(self):
        global FILE_STRUCTURE

        alpha_loc = FILE_STRUCTURE.get_file_path("alpha")
        if not os.path.exists(alpha_loc):
            return 0.5
        
        ts_dir = FILE_STRUCTURE.get_file_path("training_set")

        alpha = []

        with open(alpha_loc, "r") as f:
            for line in f:
                if not "," in line:
                    if int(line) != FileTools.count_points_in(ts_dir):
                        return 0.5
                if "," in line:
                    true_error, cv_error = tuple(line.split(","))
                    alpha.append(0.99*min(0.5*(float(true_error)/float(cv_error)), 1))

        if len(alpha) == 0:
            return 0.5
        
        return np.mean(alpha)

    def calc_epe(self, points):
        alpha = self.calc_alpha()

        logging.debug(f"Alpha: {alpha}")

        cv_errors = self.cross_validation(points)
        variances = self.variance(points)

        return alpha * cv_errors + (1-alpha) * variances

    def write_data(self, indices, points):
        global FILE_STRUCTURE

        cv_errors = self.cross_validation(points)
        predictions = self.predict(points, atoms=True)

        n_points = FileTools.count_points_in(FILE_STRUCTURE.get_file_path("training_set"))
        FileTools.mkdir(FILE_STRUCTURE.get_file_path("adaptive_sampling"))
        with open(FILE_STRUCTURE.get_file_path("cv_errors"), "w") as f:
            f.write(f"{n_points}\n")
            for index in indices:
                cv_error = cv_errors[index]
                prediction = ":".join([str(prediction) for prediction in predictions[index]])
                f.write(f"{cv_error},{prediction}\n")              

    def expected_improvement(self, points):
        global POINTS_PER_ITERATION

        best_points = np.flip(np.argsort(self.calc_epe(points)), axis=-1)
        points_to_add = best_points[:min(len(points), POINTS_PER_ITERATION)]
        self.write_data(points_to_add, points)

        return points.get_points(points_to_add)   

    def __getitem__(self, i):
        return self._models[i]
    
    def __len__(self):
        return len(self._models)


class Points:
    def __init__(self, directory="", read_gjfs=False, read_wfns=False, read_ints=False, first=False):
        self._points = []

        self.directory = directory if directory else "."
        if read_gjfs or read_wfns or read_ints:
            FileTools.check_directory(self.directory)
            self.read_directory(read_gjfs, read_wfns=read_wfns, read_ints=read_ints, first=first)

    def read_directory(self, read_gjfs, read_wfns, read_ints, first=False):
        directories = FileTools.get_files_in(self.directory, "*/", sort="natural")
        with tqdm(total=len(directories), unit=" files", leave=True) as progressbar:
            for d in directories:
                point = {"read_gjf": read_gjfs, "read_wfn": read_wfns, "read_ints": read_ints}
                point["directory"] = d
                progressbar.set_description(desc=d)
                for f in FileTools.get_files_in(d, "*", sort="natural"):
                    if os.path.isdir(f):
                        point["int_directory"] = f
                        point["int_fnames"] = FileTools.get_files_in(f, "*.int", sort="natural")
                    elif FileTools.get_filetype(f) == ".gjf":
                        point["gjf_fname"] = f
                    elif FileTools.get_filetype(f) == ".wfn":
                        point["wfn_fname"] = f
                if "gjf_fname" in point.keys():
                    self.add_point(point)
                    if first:
                        break
                progressbar.update()

    def add_point(self, point):
        if isinstance(point, dict):
            self._points.append(Point(**point))
        elif isinstance(point, Point):
            self._points.append(point)
    
    def add(self, points, move=False):
        for point in points:
            self.add_point(point)
            if move: self.move(point)

    def move(self, point):
        global SYSTEM_NAME
        old_directory = point.directory

        new_index = len(self) + 1
        subdirectory = SYSTEM_NAME + str(new_index).zfill(4)
        new_directory = os.path.join(self.directory, subdirectory)
        point.move(new_directory)

        FileTools.rmtree(old_directory)

    def get_points(self, points_to_get):
        points = Points(self.directory)
        for point in reversed(sorted(points_to_get)):
            points.add_point(self[point])
            del self[point]
        return points

    def format_gjfs(self):
        for point in self:
            if point.gjf: point.gjf.write()
    
    def submit_gjfs(self, redo=False, submit=True, hold=None, return_jid=False, modify=None):
        logging.debug("making g09 script")
        return SubmissionTools.make_g09_script(self, redo=redo, submit=submit, hold=hold, return_jid=return_jid, modify=modify)
    
    def submit_wfns(self, redo=False, submit=True, hold=None, return_jid=False, check_wfns=True):
        return SubmissionTools.make_aim_script(self, redo=redo, submit=submit, hold=hold, return_jid=return_jid, check_wfns=check_wfns)
    
    def submit_models(self):
        SubmissionTools.make_ferebus_script(self)

    def check_functional(self):
        for point in self:
            point.wfn.check_functional()

    def check_wfns(self):
        global METHOD
        global AIMALL_FUNCTIONALS

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
            if UsefulTools.in_sensitive(METHOD, AIMALL_FUNCTIONALS): 
                self.check_functional()
            print("All wfns complete.")

    def make_gjf_template(self, n_points):
        global SYSTEM_NAME
        for i in range(n_points):
            gjf_fname = os.path.join(self.directory, SYSTEM_NAME + str(i+1).zfill(4) + ".gjf")
            self.add_point(Point(gjf_fname=gjf_fname))
    
    def make_wfn_template(self, n_points):
        global SYSTEM_NAME
        for i in range(n_points):
            wfn_fname = os.path.join(self.directory, SYSTEM_NAME + str(i+1).zfill(4) + ".wfn")
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
        global FILE_STRUCTURE

        cv_file = FILE_STRUCTURE.get_file_path("cv_errors")
        if not os.path.exists(cv_file):
            return

        n_points = -1
        predictions = []
        cv_errors = []

        with open(cv_file, "r") as f:
            for line in f:
                if not "," in line:
                    n_points = int(line)
                else:
                    line = line.split(",")
                    cv_errors += [float(line[0])]
                    predictions += [[float(val) for val in line[1].split(":")]]

        new_points = FileTools.count_points_in(FILE_STRUCTURE.get_file_path("training_set"))

        true_values = []
        for point in self[n_points:]:
            true_values += [point.get_true_value("iqa", atoms=True)]

        n_points = FileTools.count_points_in(FILE_STRUCTURE.get_file_path("training_set"))
        FileTools.mkdir(FILE_STRUCTURE.get_file_path("adaptive_sampling"))
        alpha_file = FILE_STRUCTURE.get_file_path("alpha")
        with open(alpha_file, "w") as f:
            f.write(f"{n_points}\n")
            for prediction, true_value, cv_error in zip(predictions, true_values, cv_errors):
                # if None in [prediction, true_value, cv_error]:
                #     f.write("1,1\n")
                # else:
                true_error = 0
                for true_atom, predicted_atom in zip(true_value, prediction):
                    true_error += (true_atom-predicted_atom)**2
                f.write(f"{true_error},{cv_error}\n")

    def make_training_set(self, model_type):
        global FILE_STRUCTURE

        training_sets, nproperties = self.get_training_sets(model_type)
        FileTools.mkdir(FILE_STRUCTURE.get_file_path("ferebus"), empty=True)
        model_directories = []
        for atom, training_set in training_sets.items():
            directory = os.path.join(FILE_STRUCTURE.get_file_path("ferebus"), atom)
            FileTools.mkdir(directory, empty=True)
            training_set_file = os.path.join(directory, atom + "_TRAINING_SET.txt")
            with open(training_set_file, "w") as f:
                for i, line in enumerate(training_set):
                    num = f"{i+1}".zfill(4)
                    f.write(f"{line} {num}\n")
            FerebusTools.write_finput(directory, len(training_sets.keys()), atom, len(training_set),
                                      nproperties=nproperties)
            model_directories.append(directory)
        
        self.update_alpha()

        return model_directories

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

    def __len__(self):
        return FileTools.count_points_in(self.directory)
    
    def __delitem__(self, i):
        del self._points[i]

    def __getitem__(self, i):
        return self._points[i]


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
                        if re.match(r"\s*\w+(\s+[+-]?\d+.\d+([Ee]?[+-]?\d+)?){3}", line):
                            atoms.add(line)
                    atoms.finish()
                    self.add(atoms)
                    atoms = Atoms()


    def append(self, atoms):
        self._trajectory.append(atoms)

    def add_point(self, atoms):
        self.append(atoms)
    
    def add(self, atoms):
        self.append(atoms)

    def __len__(self):
        return len(self._trajectory)
    
    def __getitem__(self, i):
        return self._trajectory[i]

#############################################
#               Miscellaneous               #
#############################################

class SSH:
    def __init__(self, machine):
        global EXTERNAL_MACHINES
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
                self.ssh.connect(self.address, username=self.username, password=self.password)
                print("Connected to " + self.address)
                print()
                break
            except paramiko.ssh_exception.AuthenticationException:
                print("Username or Password is incorrect try again")
                print()
        
    def open(self):
        ncols, nrows = shutil.get_terminal_size(fallback=(80, 24))
        ncols = math.floor(ncols*0.9)
        channel = self.ssh.invoke_shell(width=ncols, height=nrows)
        self.stdin = channel.makefile('wb')
        self.stdout = channel.makefile('r')
        self.pwd

    def execute(self, cmd):
        """

        :param cmd: the command to be executed on the remote computer
        :examples:  execute('ls')
                    execute('finger')
                    execute('cd folder_name')
        """
        cmd = cmd.strip('\n')
        self.stdin.write(cmd + '\n')
        finish = 'end of stdOUT buffer. finished with exit status'
        echo_cmd = 'echo {} $?'.format(finish)
        self.stdin.write(echo_cmd + '\n')
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
    @staticmethod
    def write_control(control_file):
        global KERNEL
        global SYSTEM_NAME

        global DLPOLY_TIMESTEP
        global DLPOLY_TEMPERATURE
        global DLPOLY_PRINT_EVERY
        global DLPOLY_NUMBER_OF_STEPS

        with open(control_file, "w+") as f:
            f.write(f"Title: {SYSTEM_NAME}\n")
            f.write("# This is a generic CONTROL file. Please adjust to your requirement.\n")
            f.write("# Directives which are commented are some useful options.\n\n")
            f.write("ensemble nvt hoover 0.02\n")
            if DLPOLY_TEMPERATURE == 0:
                f.write("temperature 10.0\n\n")
                f.write("#perform zero temperature run (really set to 10K)\n")
                f.write("zero\n")
            else:
                f.write(f"temperature {DLPOLY_TEMPERATURE}\n\n")              
            f.write("# Cap forces during equilibration, in unit kT/angstrom.\n")
            f.write("# (useful if your system is far from equilibrium)\n")
            f.write("cap 100.0\n\n")
            f.write("no vdw\n\n")
            f.write(f"steps {DLPOLY_NUMBER_OF_STEPS}\n")
            f.write(f"equilibration {DLPOLY_NUMBER_OF_STEPS}\n")
            f.write(f"timestep {DLPOLY_TIMESTEP}\n")
            f.write("cutoff 15.0\n")
            f.write("fflux\n\n")
            if KERNEL.lower() != "rbf":
                f.write(f"fflux_kernel {KERNEL}")
            f.write("# Continue MD simulation\n")
            f.write("traj 0 1 2\n")
            f.write(f"print every {DLPOLY_PRINT_EVERY}\n")
            f.write(f"stats every {DLPOLY_PRINT_EVERY}\n")
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
        global SYSTEM_NAME
        global dlpoly_weights

        with open(field_file, "w") as f:
            f.write("DL_FIELD v3.00\nUnits internal\nMolecular types 1\n")
            f.write(f"Molecule name {SYSTEM_NAME}\n")
            f.write("nummols 1\n")
            f.write(f"atoms {len(atoms)}\n")
            for atom in atoms:
                f.write(f"{atom.type}\t\t{dlpoly_weights[atom.type]:.7f}     0.0   1   0\n")
            f.write("finish\nclose")

    @staticmethod
    def write_kriging(kriging_file, atoms, models):
        global SYSTEM_NAME

        atoms.calculate_alf()
        models.read()

        with open(kriging_file, "w+") as f:
            f.write(f"{SYSTEM_NAME}\t\t#prefix of model file names for the considered system\n")
            f.write(f"{len(atoms)}\t\t#number of atoms in the kriged system\n")
            f.write("3\t\t#number of moments (first 3 are to be IQA energy components xc slf src)\n")
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
        global FILE_STRUCTURE

        FileTools.mkdir(dlpoly_dir)

        control_file = os.path.join(dlpoly_dir, "CONTROL")
        config_file = os.path.join(dlpoly_dir, "CONFIG")
        field_file = os.path.join(dlpoly_dir, "FIELD")
        kriging_file = os.path.join(dlpoly_dir, "KRIGING.txt")
        dlpoly_model_dir = os.path.join(dlpoly_dir, "model_krig")

        sp_dir = FILE_STRUCTURE.get_file_path("sample_pool")

        atoms = GJF(FileTools.get_first_gjf(sp_dir), read=True)._atoms
        atoms.finish()

        DlpolyTools.write_control(control_file)
        DlpolyTools.write_config(config_file, atoms)
        DlpolyTools.write_field(field_file, atoms)
        DlpolyTools.write_kriging(kriging_file, atoms, models)
        DlpolyTools.link_models(dlpoly_model_dir, models)

    @staticmethod
    def setup_model(model_directory=None):
        global FILE_STRUCTURE

        dlpoly_dir = FILE_STRUCTURE.get_file_path("dlpoly")
        models = Models(model_directory)
        
        model_dir_name = FileTools.end_of_path(model_directory)
        dlpoly_model_dir = os.path.join(dlpoly_dir, model_dir_name)
        DlpolyTools.setup_dlpoly_dir(dlpoly_model_dir, models)

        return dlpoly_model_dir

    @staticmethod
    def run_on_model():
        global FILE_STRUCTURE
        model_dir = FILE_STRUCTURE.get_file_path("models")

        dlpoly_directories = [DlpolyTools.setup_model(model_dir)]
        SubmissionTools.make_dlpoly_script(dlpoly_directories, submit=True)

    @staticmethod
    def run_on_log():
        global SYSTEM_NAME
        global FILE_STRUCTURE

        log_dir = FILE_STRUCTURE.get_file_path("log")

        model_dirs = FileTools.get_files_in(log_dir, SYSTEM_NAME + "*/")
        dlpoly_directories = []
        for model_dir in model_dirs:
            dlpoly_directory = DlpolyTools.setup_model(model_dir)
            dlpoly_directories += [dlpoly_directory]
        
        return SubmissionTools.make_dlpoly_script(dlpoly_directories, submit=True, return_jid=True)

    @staticmethod
    @UsefulTools.externalFunc()
    def calculate_gaussian_energies():
        global FILE_STRUCTURE

        dlpoly_dir = FILE_STRUCTURE.get_file_path("dlpoly")
        trajectory_files = {}
        for model_dir in FileTools.get_files_in(dlpoly_dir, "*/"):
            trajectory_file = os.path.join(model_dir, "TRAJECTORY.xyz")
            if os.path.exists(trajectory_file):
                model_name = FileTools.end_of_path(model_dir)
                trajectory_files[model_name] = Trajectory(trajectory_file, read=True)

        for model_name, trajectory in trajectory_files.items():
            gjf_fname = os.path.join(dlpoly_dir, model_name + ".gjf")
            gjf = GJF(gjf_fname)
            gjf._atoms = trajectory[-1]
            gjf.write()

        submit_gjfs(dlpoly_dir, modify="dlpoly")

    @staticmethod
    @UsefulTools.externalFunc()
    def get_wfn_energies():
        global FILE_STRUCTURE

        dlpoly_dir = FILE_STRUCTURE.get_file_path("dlpoly")
        points = Points(dlpoly_dir, read_wfns=True)
        energy_file = os.path.join(dlpoly_dir, "Energies.txt")
        with open(energy_file, "w") as f:
            for point in points:
                if re.findall(r"\d+", point.wfn.basename):
                    point_num = int(re.findall(r"\d+", point.wfn.basename)[0])
                else:
                    point_num = 0
                f.write(f"{point.wfn.basename} {point_num:4d} {point.wfn.energy}\n")
                print(point.wfn.basename, point_num, point.wfn.energy)

    @staticmethod
    def auto_run():
        global FILE_STRUCTURE

        FileTools.rmtree(FILE_STRUCTURE.get_file_path("dlpoly"))
        FileTools.clear_log()

        log_dir = FILE_STRUCTURE.get_file_path("log")
        npoints = FileTools.count_models(log_dir)

        _, jid = DlpolyTools.run_on_log()
        _, jid = AutoTools.submit_dlpoly_gjfs(jid)
        _, jid = AutoTools.submit_gjfs(jid, npoints=npoints, modify="dlpoly")
        AutoTools.submit_dlpoly_energies(jid)


class S_CurveTools:
    vs_loc = ""
    sp_loc = ""

    log_loc = ""
    model_loc = ""

    validation_set = ""
    models = ""

    @staticmethod
    def get_dir():
        t = TabCompleter()
        t.setup_completer(t.path_completer)

        ans = input("Enter Validation Set Directory: ")
        if not os.path.isdir(ans):
            print("Invalid Input")
            print(f"{ans} is not a directory")
            print()
        else:
            return ans

    @staticmethod
    def set_vs_dir(directory=None):
        while not directory:
            directory = S_CurveTools.get_dir()
        S_CurveTools.validation_set = directory
    
    @staticmethod
    def set_model_dir(directory=None):
        while not directory:
            directory = S_CurveTools.get_dir()
        S_CurveTools.models = directory
    
    @staticmethod
    def set_model_from_log():
        global SYSTEM_NAME
        log_menu = Menu(title = "Select Model From Log", auto_close=True)
        for i, model in enumerate(FileTools.get_files_in(S_CurveTools.log_loc, "*/")):
            log_menu.add_option(f"{i+1}", model, S_CurveTools.set_model_dir, kwargs={"directory": model})
        log_menu.add_final_options(exit=False)
        log_menu.run()

    @staticmethod
    def refresh_vs_menu(menu):
        menu.clear_options()
        menu.add_option("1", f"Validation Set ({S_CurveTools.vs_loc})", S_CurveTools.set_vs_dir, kwargs={"directory": S_CurveTools.vs_loc})
        menu.add_option("2", f"Sample Pool ({S_CurveTools.sp_loc})", S_CurveTools.set_vs_dir, kwargs={"directory": S_CurveTools.sp_loc})
        menu.add_option("3", "Custom Directory", S_CurveTools.set_vs_dir)
        menu.add_space()
        menu.add_message(f"Validation Set Location: {S_CurveTools.validation_set}")
        menu.add_final_options(exit=False)
    
    @staticmethod
    def refresh_model_menu(menu):
        menu.clear_options()
        menu.add_option("1", f"Current Model ({S_CurveTools.model_loc})", S_CurveTools.set_model_dir, kwargs={"directory": S_CurveTools.model_loc})
        menu.add_option("2", f"Choose From LOG ({S_CurveTools.log_loc})", S_CurveTools.set_model_from_log)
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
        menu.add_option("1", "Calculate S-Curves", S_CurveTools.caluclate_s_curves)
        menu.add_space()
        menu.add_option("vs", "Select Validation Set Location", vs_menu.run)
        menu.add_option("model", "Select Model Location", model_menu.run)
        menu.add_space()
        menu.add_message(f"Validation Set Location: {S_CurveTools.validation_set}")
        menu.add_message(f"Model Location: {S_CurveTools.models}")
        menu.add_final_options()

    @staticmethod
    def caluclate_s_curves():
        import pandas as pd

        validation_set = Points(S_CurveTools.validation_set, read_gjfs=True, read_ints=True)
        models = Models(S_CurveTools.models, read_models=True)

        predictions = models.predict(validation_set, atoms=True)

        atom_data = {}
        for point, prediction in zip(validation_set, predictions):
            true_values = [0] * len(point.atoms)
            for atom, int_data in point.ints.items():
                if not atom in atom_data.keys():
                    atom_data[atom] = {"true": [], "predicted": [], "error": []}
                true_value = int_data.eiqa
                predicted_value = prediction[int_data.num-1]
                error = (true_value - predicted_value)**2
                
                atom_data[atom]["true"].append(true_value)
                atom_data[atom]["predicted"].append(predicted_value)
                atom_data[atom]["error"].append(error)
        
        percentages = []
        with pd.ExcelWriter("s_curves.xlsx", engine='xlsxwriter') as writer:
            errors = {}
            for atom, data in atom_data.items():
                errors[atom] = data["error"]
                df = pd.DataFrame(data)
                if not percentages:
                    percentages = [100*(i+1)/len(data["true"]) for i in range(len(data["true"]))]
                df.sort_values(by="error", inplace=True)
                df["%"] = percentages
                df.to_excel(writer, sheet_name=atom)
            df = pd.DataFrame(errors)
            df.loc[:,'Total'] = df.sum(axis=1)
            df.sort_values(by="Total", inplace=True)
            df["%"] = percentages
            df.to_excel(writer, sheet_name="Total")

    @staticmethod
    def run():
        S_CurveTools.vs_loc = FILE_STRUCTURE.get_file_path("validation_set")
        S_CurveTools.sp_loc = FILE_STRUCTURE.get_file_path("sample_pool")

        S_CurveTools.model_loc = FILE_STRUCTURE.get_file_path("models")
        S_CurveTools.log_loc = FILE_STRUCTURE.get_file_path("log")

        S_CurveTools.validation_set = S_CurveTools.vs_loc
        S_CurveTools.models = S_CurveTools.model_loc

        s_curves_menu = Menu(title="S-Curves Menu")
        # setattr(s_curves_menu, "refresh", S_CurveTools.refresh_s_curve_menu)
        s_curves_menu.set_refresh(S_CurveTools.refresh_s_curve_menu)
        s_curves_menu.run()


class SetupTools:
    @staticmethod
    def directories():
        global FILE_STRUCTURE

        directories_to_setup = [
                                "training_set",
                                "sample_pool",
                                "validation_set"
                               ]
        
        for directory in directories_to_setup:
            dir_path = FILE_STRUCTURE.get_file_path(directory)
            empty = False
            if UsefulTools.check_bool(input(f"Setup Directory: {dir_path} [Y/N]")):
                if os.path.isdir(dir_path):
                    print()
                    print(f"Warning: {dir_path} exists")
                    empty = UsefulTools.check_bool(input(f"Would you like to empty {dir_path}? [Y/N]"))
                FileTools.mkdir(dir_path, empty=empty)
            print()


class SettingsTools:
    @staticmethod
    def change(var):
        pass

    @staticmethod
    def show():
        data_types = [int, str, list, bool, None]

        settings_menu = Menu(title="Settings Menu")
        for global_var, global_val in globals().items():
            if not type(global_val) in data_types or global_var.startswith("_"):
                continue
            if global_val is None:
                global_val = "None"
            elif isinstance(global_val, list):
                global_val = "[" + ", ".join([str(val) for val in global_val]) + "]"
            else:
                global_val = str(global_val)
            global_val = "= " + global_val
            settings_menu.add_option(global_var, global_val, SettingsTools.change, kwargs={"var": global_var})
        settings_menu.add_final_options()
        settings_menu.run()
#############################################
#            Function Definitions           #
#############################################

def defineGlobals():
    global tqdm
    global ALF
    global SGE
    global MACHINE
    global SUBMITTED
    global FILE_STRUCTURE
    global DEFAULT_CONFIG_FILE

    FILE_STRUCTURE = FileTools.setup_file_structure()

    machine_name = platform.node()
    if "csf3." in machine_name:
        MACHINE = "csf3"
    elif "csf2." in machine_name:
        MACHINE = "csf2"
    elif "ffluxlab" in machine_name:
        MACHINE = "ffluxlab"
    else:
        MACHINE = "local"

    SGE = "SGE_ROOT" in os.environ.keys()
    SUBMITTED = "SGE_O_HOST" in os.environ.keys()

    if SUBMITTED:
        from tqdm import tqdm_notebook as tqdm

    check_settings = {
                      "BOAQ": "BOAQ_VALUES",
                      "IASMESH": "IASMESH_VALUES",
                      "METHOD": "GAUSSIAN_METHODS"
                     }

    default_settings = {}
    
    for setting in check_settings.keys():
        default_settings[setting] = globals()[setting]

    def to_lower(s):
        return s.lower()

    def to_upper(s):
        return s.upper()

    def replace_chars(s):
        chars_to_replace = {
                            "_": "-",
                            "\"": ""
                           }
        for char, replacement in chars_to_replace.items():
            s = s.replace(char, replacement)

        return s

    def check_str(s):
        s = replace_chars(s)
        return s

    def check_bool(val):
        return val in ['true', '1', 't', 'y', 'yes', 'yeah']

    def print_globals():
        for key, val in globals().items():
            if type(globals()[key]) in data_types.keys() and not key.startswith("_"):
                print("{:32}: {:16} ({})".format(key, str(val), type(val)))

    alf_reference_file = None

    # config reading
    config = ConfigProvider(source=DEFAULT_CONFIG_FILE)
    CONFIG = config

    data_types = {
                  int: int, 
                  str: check_str, 
                  list: ast.literal_eval, 
                  bool: check_bool
                 }

    local_values = {}
    for key, val in config.items():
        if key.lower() in locals().keys():
            if key.lower() == "alf_reference_file":
                alf_reference_file = str(val)
            continue

        if not key in globals().keys():
            print("Unknown setting found in config: " + key)
        elif key.lower() == "keywords":
            globals()[key] = val.split()
        elif type(globals()[key]) in data_types.keys() and not key.startswith("_"):
            globals()[key] = data_types[type(globals()[key])](val)

    for key, val in locals().items():
        if key in local_values.keys():
            print(key)
            locals()[key] = local_values[key]
    
    for setting, allowed_values in check_settings.items():
        if globals()[setting] not in globals()[allowed_values]:
            print("Error: Unknown " + setting + " setting")
            print("Allowed settings:")
            print(globals()[allowed_values])
            print("Setting " + setting + " to: %s" % default_settings[setting])
            globals()[setting] = default_settings[setting]

    modify_settings = {
                       "SYSTEM_NAME": to_upper,
                       "METHOD": to_upper
                      }

    for setting, modification in modify_settings.items():
        globals()[setting] = modification(globals()[setting])

    # ALF checking
    if not ALF:
        if not alf_reference_file:
            try:
                alf_reference_file = FileTools.get_files_in(FILE_STRUCTURE.get_file_path("ts_gjf"), "*.gjf")[0]
            except:
                try:
                    alf_reference_file = FileTools.get_files_in(FILE_STRUCTURE.get_file_path("sp_gjf"), "*.gjf")[0]
                except:
                    # print("\nCould not find a reference gjf to determine the ALF")
                    # print("Please specify reference file or define explicitly")
                    pass
        if alf_reference_file:
            try:
                ALF = AtomicLocalFrame(alf_reference_file)
            except:
                print("\nError in ALF calculation, please specify file to calculate ALF")

    if ALF:
        for i in range(len(ALF)):
            for j in range(len(ALF[i])):
                ALF[i][j] = int(ALF[i][j])

        if ALF[0][0] == 1:
            for i in range(len(ALF)):
                for j in range(len(ALF[i])):
                    ALF[i][j] -= 1


def readArguments():
    global AUTO_SUBMISSION_MODE
    global ITERATION
    global STEP
    global DEFAULT_CONFIG_FILE
    
    global _external_functions
    global _call_external_function
    global _call_external_function_args

    allowed_functions = ",".join(_external_functions.keys())

    parser = ArgumentParser(description="ICHOR: A kriging training suite")

    parser.add_argument("-a", "--auto", dest="auto_sub", action="store_true",
                        help="Run ICHOR in Auto Submission Mode")

    parser.add_argument("-i", "--iteration", dest="iteration", type=int, metavar='i',
                        help="Current iteration during Auto Submission Mode")

    parser.add_argument("-s", "--step", dest="step", type=int, metavar='s',
                        help="Current ICHOR step during Auto Submission Mode")
    
    parser.add_argument("-c", "--config", dest="config_file", type=str,
                        help="Name of Config File for ICHOR")
    
    parser.add_argument("-f", "--func", dest="func", type=str, metavar=("func","arg"), nargs="+",
                        help=f"Call ICHOR function with args, allowed functions: [{allowed_functions}]")

    args = parser.parse_args()

    if args.config_file:
        DEFAULT_CONFIG_FILE = args.config_file

    if args.auto_sub:
        AUTO_SUBMISSION_MODE = True

        if args.iteration:
            ITERATION = args.iteration

        if args.step:
            STEP = args.step
    
    if args.func:
        func = args.func[0]

        if len(args.func) > 1:
            args = args.func[1:]
        else:
            args = []

        if func in _external_functions:
            # UsefulTools.suppress_output()
            _call_external_function = _external_functions[func]
            _call_external_function_args = args
        else:
            print(f"{func} not in allowed functions:")
            print(f"{allowed_functions}")
            quit()


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
    global EXTERNAL_MACHINES

    ssh_menu = Menu(title="SSH Menu")
    for i, machine in enumerate(EXTERNAL_MACHINES.keys()):
        ssh_menu.add_option(f"{i+1}", machine.upper(), _ssh, kwargs={"machine": machine}, auto_close=True)
    ssh_menu.add_final_options()
    ssh_menu.run()


def auto_run():
    global MAX_ITERATION
    global FILE_STRUCTURE
    global SUBMITTED

    FileTools.clear_log()

    UsefulTools.suppress_tqdm()

    order = [
             AutoTools.submit_ichor_gjfs, 
             AutoTools.submit_gjfs, 
             AutoTools.submit_ichor_wfns,
             AutoTools.submit_wfns, 
             AutoTools.submit_ichor_models, 
             AutoTools.submit_models,
             AutoTools.submit_ichor_errors
            ]

    jid = None
    ts_dir = FILE_STRUCTURE.get_file_path("training_set")
    npoints = FileTools.count_points_in(ts_dir)

    logging.info("Starting ICHOR Auto Run")

    for i in range(MAX_ITERATION):
        for j, func in enumerate(order):
            if i == 0 and "npoints" in func.__code__.co_varnames:
                script_name, jid = func(jid, npoints)
            else:
                script_name, jid = func(jid)
            # logging.debug(f"Submitted {script_name}: {jid}")
            print(f"Submitted {script_name}: {jid}")
    
    SUBMITTED = False


@UsefulTools.externalFunc()
def submit_gjfs(directory, modify=None):
    logging.info("Submitting gjfs to Gaussian")
    gjfs = Points(directory, read_gjfs=True)
    gjfs.format_gjfs()
    gjfs.submit_gjfs(modify=modify)


@UsefulTools.externalFunc()
def submit_wfns(directory):
    logging.info("Submitting wfns to AIMAll")
    wfns = Points(directory, read_gjfs=True, read_wfns=True)
    wfns.submit_wfns()


@UsefulTools.externalFunc()
def move_models(model_file, IQA=False, copy_to_log=True):
    global FILE_STRUCTURE
    logging.info("Moving Completed Models")
    model_directory = FILE_STRUCTURE.get_file_path("models")
    FileTools.mkdir(model_directory)

    model_files = [model_file]
    if os.path.isdir(model_file):
        model_files = FileTools.get_files_in(model_file, "*_kriging_*.txt")

    for model_file in model_files:
        model = Model(model_file)
        model.remove_no_noise()

        if bool(IQA):
            model.model_type = "IQA"
        new_model_file = model.get_fname(model_directory)
        FileTools.copy_file(model_file, new_model_file)

        if copy_to_log: model.copy_to_log()


@UsefulTools.externalFunc()
def _make_models(directory, model_type):
    global _IQA_MODELS
    _IQA_MODELS = model_type.lower() == "iqa"

    logging.info(f"Making {model_type} models")

    aims = Points(directory, read_gjfs=True, read_ints=True)
    models = aims.make_training_set(model_type)
    SubmissionTools.make_ferebus_script(models)


def make_models(directory):
    model_types = ["iqa", "multipoles"]

    model_menu = Menu(title="Model Menu")
    for i, model_type in enumerate(model_types):
        model_menu.add_option(f"{i+1}", model_type.upper(), _make_models, 
                                kwargs={"directory": directory, "model_type": model_type})
    model_menu.add_final_options()

    model_menu.run()


@UsefulTools.externalFunc()
def calculate_errors(models_directory, sample_pool_directory):
    global FILE_STRUCTURE

    logging.info("Calculating errors of the Sample Pool")

    models = Models(models_directory, read_models=True)
    sample_pool = Points(sample_pool_directory, read_gjfs=True)

    points = models.expected_improvement(sample_pool)
    logging.info("Moving points to the Training Set")
    training_set_directory = FILE_STRUCTURE.get_file_path("training_set")
    training_set = Points(training_set_directory)
    training_set.add(points, move=True)
    training_set.format_gjfs()


def dlpoly_analysis():
    dlpoly_menu = Menu(title="DLPOLY Menu")
    dlpoly_menu.add_option("1", "Run DLPOLY on LOG", DlpolyTools.run_on_log)
    dlpoly_menu.add_option("2", "Run DLPOLY on current models", DlpolyTools.run_on_model)
    dlpoly_menu.add_space()
    dlpoly_menu.add_option("g", "Calculate Gaussian Energies", DlpolyTools.calculate_gaussian_energies, wait=True)
    dlpoly_menu.add_option("wfn", "Get WFN Energies", DlpolyTools.get_wfn_energies, wait=True)
    dlpoly_menu.add_space()
    dlpoly_menu.add_option("r", "Auto Run DLPOLY Analysis", DlpolyTools.auto_run)
    dlpoly_menu.add_final_options()

    dlpoly_menu.run()


def opt():
    global SYSTEM_NAME
    global FILE_STRUCTURE

    sp_dir = FILE_STRUCTURE.get_file_path("sample_pool")
    atoms = GJF(FileTools.get_first_gjf(sp_dir), read=True)._atoms

    opt_dir = FILE_STRUCTURE.get_file_path("opt")
    FileTools.mkdir(opt_dir)

    opt_gjf = GJF(os.path.join(opt_dir, SYSTEM_NAME + "1".zfill(4) + ".gjf"))
    opt_gjf._atoms = atoms
    opt_gjf.job_type="opt"
    opt_gjf.write()
    opt_gjf.submit(modify="opt")


#############################################
#                 Main Loop                 #
#############################################

def main_menu():
    global FILE_STRUCTURE
    global MACHINE

    ts_dir = FILE_STRUCTURE.get_file_path("training_set")
    sp_dir = FILE_STRUCTURE.get_file_path("sample_pool")
    vs_dir = FILE_STRUCTURE.get_file_path("validation_set")
    models_dir = FILE_STRUCTURE.get_file_path("models")

    #=== Training Set Menu ===#
    training_set_menu = Menu(title="Training Set Menu")
    training_set_menu.add_option("1", "Submit GJFs to Gaussian", submit_gjfs, kwargs={"directory": ts_dir})
    training_set_menu.add_option("2", "Submit WFNs to AIMAll", submit_wfns, kwargs={"directory": ts_dir}, wait=True)
    training_set_menu.add_option("3", "Make Models", make_models, kwargs={"directory": ts_dir})
    training_set_menu.add_space()
    training_set_menu.add_option("r", "Auto Run AIMAll", AutoTools.submit_aimall, kwargs={"directory": ts_dir})
    training_set_menu.add_final_options()

    #=== Sample Set Menu ===#
    sample_pool_menu = Menu(title="Sample Pool Menu")
    sample_pool_menu.add_option("1", "Submit GJFs to Gaussian", submit_gjfs, kwargs={"directory": sp_dir})
    sample_pool_menu.add_option("2", "Submit WFNs to AIMAll", submit_wfns, kwargs={"directory": sp_dir})
    sample_pool_menu.add_space()
    sample_pool_menu.add_option("r", "Auto Run AIMAll", AutoTools.submit_aimall, kwargs={"directory": sp_dir})
    sample_pool_menu.add_final_options()

    #=== Validation Set Menu ===#
    validation_set_menu = Menu(title="Validation Set Menu")
    validation_set_menu.add_option("1", "Submit GJFs to Gaussian", submit_gjfs, kwargs={"directory": vs_dir})
    validation_set_menu.add_option("2", "Submit WFNs to AIMAll", submit_wfns, kwargs={"directory": vs_dir})
    validation_set_menu.add_space()
    validation_set_menu.add_option("r", "Auto Run AIMAll", AutoTools.submit_aimall, kwargs={"directory": vs_dir})
    validation_set_menu.add_final_options()

    #=== Analysis Menu ===#
    analysis_menu = Menu(title="Analysis Menu")
    analysis_menu.add_option("dlpoly", "Test models with DLPOLY", dlpoly_analysis)
    analysis_menu.add_option("opt", "Perform Geometry Optimisation on First Point in Sample Pool", opt)
    analysis_menu.add_option("s", "Create S-Curves", S_CurveTools.run)
    analysis_menu.add_final_options()

    #=== Tools Menu ===#
    tools_menu = Menu(title="Tools Menu")
    tools_menu.add_option("setup", "Setup ICHOR Directories", SetupTools.directories)
    tools_menu.add_option("cp2k", "Setup CP2K run", UsefulTools.not_implemented)
    tools_menu.add_final_options()

    #=== Options Menu ===#
    options_menu = Menu(title="Options Menu")
    options_menu.add_option("settings", "Show and Change ICHOR Settings", SettingsTools.show)
    options_menu.add_option("ssh", "SSH into external machine", ssh)
    options_menu.add_final_options()

    #=== Queue Menu ===#
    queue_menu = Menu(title="Queue Menu")
    queue_menu.add_option("stat", "Get qstat", BatchTools.qstat, wait=True)
    queue_menu.add_option("del", "Get qdel running jobs", BatchTools.qdel, wait=True)
    queue_menu.add_final_options()

    #=== Main Menu ===#
    main_menu = Menu(title="ICHOR Main Menu", enable_problems=True, message=f"Running on {MACHINE}", auto_clear=True)
    main_menu.add_option("1", "Training Set", training_set_menu.run)
    main_menu.add_option("2", "Sample Pool", sample_pool_menu.run)
    main_menu.add_option("3", "Validation Set", validation_set_menu.run)
    main_menu.add_option("4", "Calculate Errors", calculate_errors, kwargs={"models_directory": models_dir, 
                                                                            "sample_pool_directory": sp_dir}, wait=True)
    main_menu.add_space()
    main_menu.add_option("r", "Auto Run", auto_run)
    main_menu.add_space()
    main_menu.add_option("a", "Analysis", analysis_menu.run)
    main_menu.add_option("t", "Tools", tools_menu.run)
    main_menu.add_option("o", "Options", options_menu.run)
    main_menu.add_option("q", "Queue", queue_menu.run)

    main_menu.add_option("dlpoly", "DLPOLY Analysis Options", dlpoly_analysis, hidden=True)

    main_menu.add_final_options(back=False)
    main_menu.run()


if __name__ == "__main__":
    readArguments()
    defineGlobals()
    
    if not _call_external_function is None:
        _call_external_function(*_call_external_function_args)
        quit()

    if len(glob("*.sh.*")) > 0:
        os.system("rm *.sh.*")

    main_menu()
