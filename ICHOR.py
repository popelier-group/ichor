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
  Version: 0.2

  ICHOR Design Principles:
  -- All within one script, this is up for debate however this script currently requires high portabilty and therefore
     is being designed within one script
  -- GLOBALS are in all caps and defined at the top of the script below the import statements
  -- Classes are defined next
  -- Functions are defined after Classes
  -- Main script is written beneath which calls functions when needed
  -- Main Menu is at the bottom, this should be easy to extend and is hopefully quite intuitive

"""

import sys
import shutil
from glob import glob
import os
import re
from time import gmtime, strftime
import math
import subprocess
from subprocess import Popen
from datetime import date
from datetime import datetime
from typing import List, Any, Union

import numpy as np
from numpy import linalg as la
import ast
from decimal import Decimal
from operator import itemgetter
import uuid
from argparse import ArgumentParser
from numpy.core.multiarray import ndarray
import itertools
from tqdm import tqdm
import tqdm as tq

"""

 ################################################################################
 #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::#
 #::##########################################################################::#
 #::#                                                                        #::#
 #::#   ,ad8888ba,   88               88                       88            #::#
 #::#  d8"'    `"8b  88               88                       88            #::#
 #::# d8'            88               88                       88            #::#
 #::# 88             88   ,adPPYba,   88,dPPYba,   ,adPPYYba,  88  ,adPPYba, #::#
 #::# 88      88888  88  a8"     "8a  88P'    "8a  ""     `Y8  88  I8[    "" #::#
 #::# Y8,        88  88  8b       d8  88       d8  ,adPPPPP88  88   `"Y8ba,  #::#
 #::#  Y8a.    .a88  88  "8a,   ,a8"  88b,   ,a8"  88,    ,88  88  aa    ]8I #::#
 #::#   `"Y88888P"   88   `"YbbdP"'   8Y"Ybbd8"'   `"8bbdP"Y8  88  `"YbbdP"' #::#
 #::#                                                                        #::#
 #::##########################################################################::#
 #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::#
 ################################################################################

"""

DEFAULT_CONFIG_FILE = "config.properties"
CONFIG = None

SYSTEM_NAME = "WATER"
ALF = []

AUTO_SUBMISSION_MODE = False
MAX_ITERATION = 1
POINTS_PER_ITERATION = 1

MULTIPLE_ADDITION_MODE = "multiple"

ITERATION = 0
STEP = 0

FORMAT_GJFS = True
POTENTIAL = "B3LYP"
BASIS_SET = "6-31+g(d,p)"

ENCOMP = 3

EXIT = False

FILE_STRUCTURE = []
IMPORTANT_FILES = {}

TRAINING_POINTS = []
SAMPLE_POINTS = []

TRAINING_POINTS_TO_USE = None

KERNEL = "rbf"                # only use rbf for now
FEREBUS_VERSION = "python"    # fortran (FEREBUS) or python (FEREBUS.py)

# CORE COUNT SETTINGS FOR RUNNING PROGRAMS (SUFFIX CORE_COUNT)
GAUSSIAN_CORE_COUNT = 2
AIMALL_CORE_COUNT = 2
FEREBUS_CORE_COUNT = 4
DLPOLY_CORE_COUNT = 1

# DLPOLY RUNTIME SETTINGS (PREFIX DLPOLY)
DLPOLY_NUMBER_OF_STEPS=500    # Number of steps to run simulation for
DLPOLY_TEMPERATURE = 0        # If set to 0, will perform geom opt but default to 10 K
DLPOLY_PRINT_EVERY = 1        # Print trajectory and stats every n steps
DLPOLY_TIMESTEP = 0.001       # in ps

MACHINE = "csf3"

TRAINING_SET = None

NORMALIZE = False
PREDICTION_MODE = "george"    # ichor or george (recommend george)

PRECALCULATE_AIMALL = True


"""
 ################################################################################
 #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::#
 ################################################################################
"""


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
            f.write(UsefulTools.get_ichor_logo())
            f.write("\n")
            for key in self:
                f.write("%s=%s\n" % (key, self[key]))


def sanitize_id(node_id):
    return node_id.strip().replace(" ", "")


(_ADD, _DELETE, _INSERT) = range(3)
(_ROOT, _DEPTH, _WIDTH) = range(3)


class Node:

    def __init__(self, name, identifier=None, expanded=True):
        self.__identifier = (str(uuid.uuid1()) if identifier is None else sanitize_id(str(identifier)))
        self.name = name
        self.expanded = expanded
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

    def create_node(self, name, identifier=None, parent=None):
        node = Node(name, identifier)
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
        return os.path.join(*list(reversed(file_path[:-1])), '')

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


class Constants:

    PI = math.pi
    TAU = 2 * math.pi
    
    rt3 = math.sqrt(3)
    rt5 = math.sqrt(5)

    div5_3 = 5.0 / 3.0


class GJF:

    def __init__(self, name, potential="B3LYP", basis_set="6-31+g(d,p)"):
        self.name = name
        self.potential = potential
        self.basis_set = basis_set

        self.base = self.get_base()

        self.coordinates = []

        self.nproc = 2
        self.mem = "2000mb"

        self.keywords = []

        self.opt = False
        self.output_wfn = True
        self.charge = 0
        self.multiplicity = 1

        self.gen_basis = None

    def get_base(self):
        return self.name.replace(".gjf", "")

    def change_basis_set(self, basis_set):
        self.basis_set = basis_set

    def change_potential(self, potential):
        self.potential = potential

    def change_nproc(self, nproc):
        self.nproc = nproc

    def set_optmise(self, opt):
        self.opt = opt

    def gen_basis_set(self, basis_set):
        self.gen_basis =basis_set

    def add_keyword(self, keyword):
        self.keywords.append(keyword)

    def add_keywords(self, keywords):
        for keyword in keywords:
            self.keywords.append(keyword)

    def add_coordinates(self, coordinates):
        for i in range(len(coordinates)):
            if not coordinates[i].endswith("\n"):
                coordinates[i] += "\n"
        self.coordinates = coordinates


    def add_coordinate(self, coordinate):
        if not coordinate.endswith("\n"):
            coordinate += "\n"
        self.coordinates.append(coordinate)

    def change_output_wfn(self, output_wfn):
        self.output_wfn = output_wfn

    def change_mem(self, nproc):
        self.nproc = nproc

    def set_charge_multiplicity(self, charge=0, multiplicity=1):
        self.charge = charge
        self.multiplicity = multiplicity

    def defBasisSet(self, basis_set):
        # Need to make a nice commented list of Available Basis Sets, as well as form a way for this not to be hard coded
        # Could Make option to select between available basis sets

        bs = ""
        if basis_set == "truncated":
            bs = "       1  0 \n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.1533000000D+05  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.2299000000D+04  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.5224000000D+03  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.1473000000D+03  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.4755000000D+02  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.1676000000D+02  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.6207000000D+01  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.6882000000D+00  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.1752000000D+01  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.2384000000D+00  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.7376000000D-01  0.1000000000D+01\n" \
                 " P   1 1.00       0.000000000000\n" \
                 "     0.3446000000D+02  0.1000000000D+01\n" \
                 " P   1 1.00       0.000000000000\n" \
                 "     0.7749000000D+01  0.1000000000D+01\n" \
                 " P   1 1.00       0.000000000000\n" \
                 "     0.2280000000D+01  0.1000000000D+01\n" \
                 " P   1 1.00       0.000000000000\n" \
                 "     0.7156000000D+00  0.1000000000D+01\n" \
                 " P   1 1.00       0.000000000000\n" \
                 "     0.2140000000D+00  0.1000000000D+01\n" \
                 " P   1 1.00       0.000000000000\n" \
                 "     0.5974000000D-01  0.1000000000D+01\n" \
                 " D   1 1.00       0.000000000000\n" \
                 "     0.2314000000D+01  0.1000000000D+01\n" \
                 " D   1 1.00       0.000000000000\n" \
                 "     0.6450000000D+00  0.1000000000D+01\n" \
                 " D   1 1.00       0.000000000000\n" \
                 "     0.2140000000D+00  0.1000000000D+01\n" \
                 " ****\n" \
                 "     2 3 0\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.3387000000D+02  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.5095000000D+01  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.1159000000D+01  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.3258000000D+00  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.1027000000D+00  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.2526000000D-01  0.1000000000D+01\n" \
                 " P   1 1.00       0.000000000000\n" \
                 "     0.1407000000D+01  0.1000000000D+01\n" \
                 " P   1 1.00       0.000000000000\n" \
                 "     0.3880000000D+00  0.1000000000D+01\n" \
                 " P   1 1.00       0.000000000000\n" \
                 "     0.1020000000D+00  0.1000000000D+01\n" \
                 " ****\n"
        else:
            bs = "Unkown Basis Set\n"
        return bs

    def get_header(self):
        header_string = "#"
        if self.opt:
            header_string += "opt "
        else:
            header_string += "p "
        header_string += "%s/%s " % (self.potential, self.basis_set)
        if self.output_wfn:
            header_string += "output=wfn "
        for keyword in self.keywords:
            header_string += "%s " % keyword

        return header_string + "\n\n"

    def write_gjf(self):
        with open(self.name, "w+") as f:
            f.write("%%mem=%s\n" % self.mem)
            f.write("%%nproc=%d\n" % self.nproc)
            f.write(self.get_header())
            f.write("%s\n\n" % self.base)
            f.write(" %d %d\n" % (self.charge, self.multiplicity))
            for coordinate in self.coordinates:
                f.write(coordinate)
            f.write("\n")
            if self.basis_set == "gen":
                f.write(self.defBasisSet(self.gen_basis))
                f.write("\n")
            if self.output_wfn:
                f.write("%s.wfn" % self.base)


class Atom:

    def __init__(self, atom_type=None, x=None, y=None, z=None):
        self.atom_type = atom_type.upper()
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    
    def coordinate_list(self):
        return [self.x, self.y, self.y]
    
    def coordinate_line(self):
        return "%s%10f%10f%10f" % (self.atom_type, self.x, self.y, self.z)
    
    def __repr__(self):
        return "%s%10f%10f%10f" % (self.atom_type, self.x, self.y, self.z)


class GJF_file:

    def __init__(self, fname):
        self.fname = fname
        self.output = fname.replace(".gjf", ".log")
        self.name = Point.get_name(fname)

        self.title = None
        self.run_type = None
        self.startup_options = []

        self.potential = None
        self.basis_set = None

        self.keywords = []

        self.charge = None
        self.multiplicity = None

        self.coordinates = []

        self.gen_basis_set = ""

        self.output_wfn = False
        self.output_wfn_fname = None

        self.parse_gjf()
    
    def parse_gjf(self):
        try:
            with open(self.fname, "r") as f:
                for line in f:
                    if line.startswith("%"):
                        self.startup_options.append(line.strip())
                    elif line.startswith("#"):
                        line_split = line.replace("#", "").split()
                        for item in line_split:
                            if "/" in item:
                                item_split = item.split("/")
                                self.potential = item_split[0]
                                self.basis_set = item_split[1]
                            elif item.lower() == "output=wfn":
                                self.output_wfn = True
                                self.keywords.append(item)
                            else:
                                self.keywords.append(item)
                    elif re.match("\s*\d+\s+\d+", line) and not self.charge and not self.multiplicity:
                        line_split = re.findall("\d+", line)
                        self.charge = int(line_split[0])
                        self.multiplicity = int(line_split[1])

                    elif re.match("\s*\w+(\s+[+-]?\d+.\d+){3}", line):
                        line_split = line.split()
                        self.coordinates.append(Atom(atom_type=line_split[0], x=line_split[1], y=line_split[2], z=line_split[3]))
                    elif ".wfn" in line:
                        self.output_wfn_fname = line.strip()
                    elif not self.title:
                        self.title = line.strip()
                    elif self.basis_set == "gen":
                        if line.strip():
                            self.gen_basis_set += line
        except:
            print("\nError: Cannot Read File %s" % self.fname)
   
    def set_default_wfn(self):
        self.output_wfn_fname = self.fname.replace(".gjf", ".wfn")
 
    def set_gen_basis_set(self, gen_basis_set):
        self.basis_set = "gen"
        self.gen_basis_set = self.get_gen_basis_set(gen_basis_set)
    
    def optimise(self):
        opt_keyword = "opt"
        if "p" in self.keywords:
            for i, keyword in enumerate(self.keywords):
                if keyword == "p":
                    self.keywords[i] = opt_keyword
        elif "opt" not in self.keywords:
            self.keywords.append(opt_keyword)

    def get_gen_basis_set(self, basis_set):
        # Need to make a nice commented list of Available Basis Sets, as well as form a way for this not to be hard coded
        # Could Make option to select between available basis sets

        bs = ""
        if basis_set == "truncated":
            bs = "       1  0 \n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.1533000000D+05  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.2299000000D+04  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.5224000000D+03  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.1473000000D+03  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.4755000000D+02  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.1676000000D+02  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.6207000000D+01  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.6882000000D+00  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.1752000000D+01  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.2384000000D+00  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.7376000000D-01  0.1000000000D+01\n" \
                 " P   1 1.00       0.000000000000\n" \
                 "     0.3446000000D+02  0.1000000000D+01\n" \
                 " P   1 1.00       0.000000000000\n" \
                 "     0.7749000000D+01  0.1000000000D+01\n" \
                 " P   1 1.00       0.000000000000\n" \
                 "     0.2280000000D+01  0.1000000000D+01\n" \
                 " P   1 1.00       0.000000000000\n" \
                 "     0.7156000000D+00  0.1000000000D+01\n" \
                 " P   1 1.00       0.000000000000\n" \
                 "     0.2140000000D+00  0.1000000000D+01\n" \
                 " P   1 1.00       0.000000000000\n" \
                 "     0.5974000000D-01  0.1000000000D+01\n" \
                 " D   1 1.00       0.000000000000\n" \
                 "     0.2314000000D+01  0.1000000000D+01\n" \
                 " D   1 1.00       0.000000000000\n" \
                 "     0.6450000000D+00  0.1000000000D+01\n" \
                 " D   1 1.00       0.000000000000\n" \
                 "     0.2140000000D+00  0.1000000000D+01\n" \
                 " ****\n" \
                 "     2 3 0\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.3387000000D+02  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.5095000000D+01  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.1159000000D+01  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.3258000000D+00  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.1027000000D+00  0.1000000000D+01\n" \
                 " S   1 1.00       0.000000000000\n" \
                 "     0.2526000000D-01  0.1000000000D+01\n" \
                 " P   1 1.00       0.000000000000\n" \
                 "     0.1407000000D+01  0.1000000000D+01\n" \
                 " P   1 1.00       0.000000000000\n" \
                 "     0.3880000000D+00  0.1000000000D+01\n" \
                 " P   1 1.00       0.000000000000\n" \
                 "     0.1020000000D+00  0.1000000000D+01\n" \
                 " ****\n"
        else:
            bs = "Unkown Basis Set\n"
        return bs

    def add_keyword(self, keyword):
        if keyword not in self.keywords:
            self.keywords.append(keyword)

    def add_keywords(self, keywords):
        for keyword in keywords:
            self.add_keyword(keyword)

    def remove_connectivity(self):
        for i, keyword in enumerate(self.keywords):
            if keyword == "geom=connectivity":
                del self.keywords[i]

    def write_gjf(self):
        with open(self.fname, "w") as f:
            for startup_option in self.startup_options:
                f.write("%s\n" % startup_option)
            
            f.write("#%s/%s %s\n\n" % (self.potential, self.basis_set, " ".join(self.keywords)))
            
            f.write("%s\n\n" % self.fname.replace(".gjf", ""))
            
            f.write(" %d %d\n" % (self.charge, self.multiplicity))
            for atom in self.coordinates:
                f.write("%s%16.8f%16.8f%16.8f\n" % (atom.atom_type, atom.x, atom.y, atom.z))
            f.write("\n")
            if self.basis_set.lower() == "gen":
                f.write(self.get_gen_basis_set("truncated"))
                f.write("\n")
            f.write("%s" % self.output_wfn_fname)

    def __str__(self):
        coordinates = [str(c) for c in self.coordinates]
        return "FileName:         {}\n"\
                "Output:          {}\n"\
                "Name:            {}\n\n"\
                "Title:           {}\n"\
                "Run Type:        {}\n"\
                "StartUp Options: [{}]\n\n"\
                "Potential:       {}\n"\
                "Basis Set:       {}\n\n"\
                "Keywords:        [{}]\n\n"\
                "Charge:          {}\n"\
                "Multiplicity:    {}\n"\
                "Coordinates:\n   {}\n\n"\
                "GenBasis:        {}\n\n"\
                "OutputWFN:       {}\n"\
                "WFN FileName:    {}".format(
                    self.fname,
                    self.output,
                    self.name,
                    self.title,
                    self.run_type,
                    ",".join(self.startup_options),
                    self.potential,
                    self.basis_set,
                    ",".join(self.keywords),
                    self.charge,
                    self.multiplicity,
                    "\n".join(coordinates),
                    self.gen_basis_set,
                    self.output_wfn,
                    self.output_wfn_fname
                )
                

    def __repr__(self):
        return str(self)


class WFN:

    def __init__(self, fname, readFile=True):
        self.fname = fname
        if self.fname:
            try:
                self.energy = self.get_energy()
            except:
                pass

    def getLastLine(self, maxLineLength=80):
        with open(self.fname, "rb") as f:
            f.seek(-maxLineLength - 1, 2)  # 2 means "from the end of the file"
            return f.readlines()[-1].decode('utf-8')

    def get_energy(self):
        last_line = self.getLastLine()
        energy = float(re.findall("[+-]?\d+.\d+", last_line)[0])
        return energy


class INT:

    def __init__(self, fname, read_file=True):
        self.fname = fname

        self.int_name = self.fname.split("/")[-1]
        self.name = self.int_name.split("_")[0]
        self.atom = self.int_name.replace(".int", "").split("_")[-1].upper()

        self.charge = 0
        self.integrationError = 0
        self.multipole_moments = {}
        self.IQA_terms = {}

        if read_file:
            self.read_int()

    def read_int(self):
        line_counter = 0
        with open(self.fname, "r") as f:
            content = f.readlines()
            while line_counter < len(content):
                if " Results of the basin integration:" in content[line_counter]:
                    line_counter += 1
                    line_split = content[line_counter].split("=")
                    self.charge = float(line_split[2])
                    line_counter += 3
                    self.integrationError = float(content[line_counter].split("=")[-1])

                if " Real Spherical Harmonic Moments Q[l,|m|,?]" in content[line_counter]:
                    line_counter += 4
                    while "=" in content[line_counter]:
                        line_split = content[line_counter].split("=")
                        multipole_moment = line_split[0].strip().replace(",", "")\
                                            .replace("[", "").replace("]", "").lower()
                        self.multipole_moments[multipole_moment] = float(line_split[-1])

                        line_counter += 1

                if "IQA Energy Components (see \"2EDM Note\"):" in content[line_counter]:
                    line_counter += 2
                    while "=" in content[line_counter]:
                        line_split = content[line_counter].split("=")
                        iqa_term = line_split[0].strip()
                        self.IQA_terms[iqa_term] = float(line_split[-1])

                        line_counter += 1
                    break

                line_counter += 1


class MODEL:

    def __init__(self, fname, read_model=True):
        global KERNEL
        global PREDICTION_MODE

        self.fname = fname
        self.type = self.fname.split(".")[0].split("_")[-2]
        self.number = self.fname.split(".")[0].split("_")[-1]

        self.nFeats = 0
        self.nTrain = 0

        self.mu = 0.0
        self.sigma_squared = 0.0
        self.theta_values = []
        self.p_values = []
        self.weights = []
        self.inv_R = np.empty(1)

        self.kriging_centres = np.empty(1)
        self.training_data = np.empty(1)

        if "matern52" in KERNEL or "matern5" in KERNEL:
            self.correlation = self.matern52_correlation
        else:
            self.correlation = self.gaussian_correlation
        
        if PREDICTION_MODE == "george":
            self.predict = self.predict_george
            self.variance = self.variance_george
        else:
            self.predict = self.predict_ichor
            self.variance = self.variance_ichor
            if "matern52" in KERNEL or "matern5" in KERNEL:
                self.correlation = self.matern52_correlation
            else:
                self.correlation = self.gaussian_correlation
        


        if read_model:
            self.read_model()

    def read_model(self):
        with open(self.fname, "r") as f:
            content = f.readlines()
            line_i = 0
            while line_i < len(content):
                if "Feature" in content[line_i]:
                    self.nFeats = int(re.findall("\d+", content[line_i])[0])

                if "Number_of_training_points" in content[line_i]:
                    self.nTrain = int(re.findall("\d+", content[line_i])[0])
                    self.inv_R = np.resize(self.inv_R, self.nTrain ** 2)
                    self.kriging_centres = np.resize(self.kriging_centres, (self.nTrain, 1))
                    self.training_data = np.resize(self.training_data, self.nTrain * self.nFeats)

                if "Mu" in content[line_i]:
                    line_split = content[line_i].split()
                    self.mu = float(line_split[1])
                    self.sigma_squared = float(line_split[3])

                if content[line_i].strip() == "Theta":
                    line_i += 1
                    while ";" not in content[line_i]:
                        self.theta_values.append(float(content[line_i]))
                        line_i += 1

                if content[line_i].strip() == "p":
                    line_i += 1
                    while ";" not in content[line_i]:
                        self.p_values.append(float(content[line_i]))
                        line_i += 1

                if content[line_i].strip() == "Weights":
                    line_i += 1
                    while ";" not in content[line_i]:
                        self.weights.append(float(content[line_i]))
                        line_i += 1

                if content[line_i].strip() == "R_matrix":
                    line_i += 2
                    points = 0
                    while ";" not in content[line_i]:
                        nums = content[line_i].split()
                        for num in nums:
                            self.inv_R[points] = float(num)
                            points += 1
                        line_i += 1

                if "Property_value_Kriging_centers" in content[line_i]:
                    line_i += 1
                    point = 0
                    while "training_data" not in content[line_i]:
                        self.kriging_centres[point][0] = float(re.findall("-?\d+.?\d*(?:[Ee]-\d+)?",
                                                                          content[line_i])[0])
                        point += 1
                        line_i += 1

                    line_i += 1
                    points = 0
                    while ";" not in content[line_i]:
                        nums = content[line_i].split()
                        for num in nums:
                            self.training_data[points] = float(num)
                            points += 1
                        line_i += 1
                    break

                line_i += 1

            self.inv_R = self.inv_R.reshape(self.nTrain, self.nTrain)
            self.training_data = self.training_data.reshape(self.nTrain, self.nFeats)

    def gaussian_correlation(self, xi, xj):
        correlation = 0
        for h in range(self.nFeats):
            diff = abs(xi[h] - xj[h])
            correlation += self.theta_values[h] * diff * diff
        return np.exp(-correlation)

    def matern52_correlation(self, xi, xj):
        correlation = 0
        for h in range(self.nFeats):
            diff = abs(xi[h] - xj[h])
            theta_diff = np.sqrt(self.theta_values[h]) * diff
            theta_diff2 = self.theta_values[h] * diff * diff
            correlation += (1 + Constants.rt5 *  theta_diff + Constants.div5_3 * theta_diff2) * np.exp(-Constants.rt5 * theta_diff)
        return correlation

    def predict_ichor(self, x_values):
        predictions = np.empty(shape=(len(x_values)))
        for i in range(len(x_values)):
            r = np.empty(shape=(self.nTrain))
            for j in range(self.nTrain):
                r[j] = self.correlation(x_values[i], self.training_data[j])

            predictions[i] = self.mu + np.dot(np.matmul(r.T, self.inv_R), (self.kriging_centres - self.mu))

        return predictions

    def variance_ichor(self, x_values):
        s_values = np.empty(shape=(len(x_values)))
        ones = np.ones(shape=(self.nTrain))
        res3 = np.dot(np.matmul(ones.T, self.inv_R), ones)
        for i in range(len(x_values)):
            r = np.empty(shape=(self.nTrain))
            for j in range(self.nTrain):
                r[j] = self.correlation(x_values[i], self.training_data[j])

                res1 = np.dot(np.matmul(r.T, self.inv_R), r)
                res2 = np.dot(np.matmul(ones.T, self.inv_R), r)

            s_values[i] = self.sigma_squared * (1 - res1 + (1 - res2)**2/res3)

        return s_values

    def predict_george(self, x_values):
        global KERNEL
        import george

        x_values = np.array(x_values).reshape((-1, self.nFeats))

        x_train = np.array(self.training_data).reshape((self.nTrain, self.nFeats))
        y_train = np.array(self.kriging_centres).reshape((self.nTrain,))

        if "matern52" in KERNEL or "matern5" in KERNEL:
            from george.kernels import Matern52Kernel as Kernel
            thetas = np.exp(-np.log(np.array(self.theta_values)))
        else:
            from george.kernels import ExpSquaredKernel as Kernel
            thetas = np.exp(-np.log(2*np.array(self.theta_values)))

        kernel = Kernel(thetas, ndim=self.nFeats)
        gp = george.GP(kernel, mean=self.mu, fit_mean=True, white_noise=np.log(1e-30), fit_white_noise=False)
        gp.compute(x_train)
        preds = gp.predict(y_train, x_values, return_cov=False, return_var=False)
        
        return preds

    def variance_george(self, x_values):
        global KERNEL
        import george

        x_values = np.array(x_values).reshape((-1, self.nFeats))

        x_train = np.array(self.training_data).reshape((self.nTrain, self.nFeats))
        y_train = np.array(self.kriging_centres).reshape((self.nTrain,))

        if "matern52" in KERNEL or "matern5" in KERNEL:
            from george.kernels import Matern52Kernel as Kernel
            thetas = np.exp(-np.log(np.array(self.theta_values)))
        else:
            from george.kernels import ExpSquaredKernel as Kernel
            thetas = np.exp(-np.log(2*np.array(self.theta_values)))

        kernel = Kernel(thetas, ndim=self.nFeats)
        gp = george.GP(kernel, mean=self.mu, fit_mean=True, white_noise=np.log(1e-30), fit_white_noise=False)
        gp.compute(x_train)
        _, var = gp.predict(y_train, x_values, return_cov=False, return_var=True)

        return var

    def __calcCVErrorOld(self):
        cv_errors = []

        B = np.empty(self.nTrain)
        F = np.full((self.nTrain, 1), self.mu)

        H = np.matmul(F, np.matmul(la.inv(np.matmul(F.T, F)), F.T))
        Beta = np.matmul(la.inv(np.matmul(F.T, np.matmul(self.inv_R, F))),
                         np.matmul(F.T, np.matmul(self.inv_R, self.kriging_centres)))
        d = (self.kriging_centres - np.matmul(F, Beta)).reshape(self.nTrain, 1)

        for i in range(self.nTrain):
            h = H[:, i].reshape(self.nTrain, 1)
            r = self.inv_R[i, :].reshape(self.nTrain, 1)
            di = np.matmul(h, d[i] / (1 - H[i, i])).reshape(self.nTrain, 1)
            e_cv = (np.matmul(r, (d + di).T)[0, 0] / self.inv_R[i, i])**2
            cv_errors.append(e_cv)

        return cv_errors
    
    def calcCVError(self):
        cv_errors = []
        
        F = np.ones((self.nTrain, 1))
        
        FTR = np.matmul(F.T, self.inv_R)
        B = np.matmul(la.inv(np.matmul(FTR, F)), np.matmul(FTR, self.kriging_centres))
        H = np.matmul(F, np.matmul(la.inv(np.matmul(F.T, F)), F.T))
        
        d = (self.kriging_centres - np.matmul(F, B)).reshape((-1, 1))
        cv_errors = np.empty(self.nTrain)
        
        for i in range(self.nTrain):
            e_cv = np.matmul(self.inv_R[i, :], (d + H[:,i].reshape(-1, 1) * d[i]/(1-H[i,i]))) / self.inv_R[i, i]
            cv_errors[i] = e_cv**2
        
        return list(cv_errors)


class Point:

    name = None

    def __init__(self, gjf=None, wfn=None, int_directory=None):
        
        self.wfn = WFN(wfn)
        self.int = {}
        self.features = {}
        self.set_gjf_file(gjf)
        try:
            self.read_int_files(int_directory)
        except:
            pass
        
        self.set_point_name()

    def set_gjf_file(self, gjf_fname):
        try:
            self.gjf = GJF_file(gjf_fname)
            self.geometry = self.gjf.coordinates
        except:
            self.gjf = None

    def read_int_files(self, int_dir):
        int_files = FileTools.get_files_in(int_dir, "*.int")
        for int_file in int_files:
            self.read_int_file(int_file)

    def add_int_file(self, fname):
        self.read_int_file(fname)
    
    def read_int_file(self, fname):
        try:
            int_data = INT(fname)
            self.int[int_data.atom] = int_data
        except:
            print("\nError: Cannot Read File %s" % fname)
    
    def calculate_features(self):
        global ALF
        if not self.features:
            try:
                coordinates = [[atom.x, atom.y, atom.z] for atom in self.gjf.coordinates]
                self.feats = calcFeats(ALF, coordinates)
                for i in range(len(self.gjf.coordinates)):
                    self.features["%s%d" % (self.gjf.coordinates[i].atom_type, i+1)] = self.feats[i]
            except:
                print("Error calculating features for point: %s" %self.name)
                self.features = None

    
    @staticmethod
    def get_name(name):
        return os.path.split(name)[1].split(".")[0].split("_")[0]

    def set_point_name(self):
        try:
            self.name = self.get_name(self.gjf.name)
        except:
            try:
                self.name = self.get_name(self.wfn_fname)
            except:
                try:
                    for atom, _ in self.int.items():
                        self.name = self.get_name(self.int[atom].fname)
                except:
                    self.name = None
    
    def get_training_set_line(self, IQA=True):
        self.training_set_lines = {}
        for atom, int_data in self.int.items():
            features = [str(x) for x in self.features[atom]]

            if IQA:
                training_data = [str(int_data.IQA_terms["E_IQA(A)"])]
            else:
                training_data = [str(data[1]) for data in int_data.multipole_moments.items()][:25]
            
            for _ in range(len(training_data), 25):
                training_data.append("0")

            line = "%s  %s" % ("  ".join(features), "  ".join(training_data))

            self.training_set_lines[atom] = line


class Points:

    def __init__(self, gjfs=[], wfns=[], int_directories=[], training_set=False):
        self.training_set = training_set
        self.points = []
        if gjfs or wfns or int_directories:
            self.form_set(gjfs=gjfs, wfns=wfns, int_directories=int_directories)

    def add_point(self, gjf_file=None, wfn_file=None, int_directory=None):
        gjf_name = FileTools.get_base(gjf_file) if gjf_file else None
        wfn_name = FileTools.get_base(wfn_file) if wfn_file else None
        int_name = FileTools.get_base(int_directory) if int_directory else None
        
        names = [gjf_name, wfn_name, int_name]
        for point in self.points:
            if point.name in names:
                if gjf_file:
                    try:
                        point.gjf = GJF_file(gjf_file)
                    except:
                        point.gjf = None
                
                if wfn_file:
                    try:
                        point.wfn_fname = WFN(wfn_file)
                    except:
                        point.wfn_fname = None
                
                if int_directory:
                    try:
                        point.int = point.read_int_files(int_directory)
                    except:
                        point.int = None
                break
        else:
            self.points.append(Point(gjf=gjf_file, wfn=wfn_file, int_directory=int_directory))

    def format_gjfs(self, potential=None, basis_set=None, charge=None, multiplicity=None, keywords=[], remove_connectivity=True):
        global POTENTIAL
        global BASIS_SET
        
        for point in self:
            if potential:
                point.gjf.potential = potential
            else:
                point.gjf.potential = POTENTIAL

            if basis_set:
                point.gjf.basis_set = basis_set
            else:
                point.gjf.basis_set = BASIS_SET

            if charge:
                point.gjf.charge = charge
            else:
                point.gjf.charge = 0

            if multiplicity:
                point.gjf.multiplicity = multiplicity
            else:
                point.gjf.multiplicity = 1

            for keyword in keywords:
                point.gjf.add_keyword(keyword)

            if remove_connectivity:
                point.gjf.remove_connectivity()

            point.gjf.set_default_wfn()

    def make_training_set(self, IQA=True, writeSet=True, directory=None):
        if not directory:
            global FILE_STRUCTURE
            fereb_dir = FILE_STRUCTURE.get_file_path("ts_ferebus")

        for point in self.points:
            point.calculate_features()
            point.get_training_set_line(IQA=IQA)

        nproperties = {True: 1, False: 25}

        self.training_set_directories = []

        atoms = self.get_atoms()
        for atom in atoms:
            atom_dir = os.path.join(fereb_dir, atom)
            FileTools.make_clean_directory(atom_dir)
            FerebusTools.write_finput(atom_dir, len(atoms), atom, len(self.points), nproperties=nproperties[IQA])

            self.training_set_directories.append(atom_dir)

            training_set_file = os.path.join(atom_dir, atom + "_TRAINING_SET.txt")
            with open(training_set_file, "w+") as f:
                for i, training_point in enumerate(self.points):
                    f.write("%s  %s\n" % (training_point.training_set_lines[atom], str(i+1).zfill(4)))
    
    def predict(self, models):
        features = []
        for point in self:
            point.calculate_features()
            point_features = [x[1] for x in point.features.items()]
            features.append(point_features)

        x_values = []
        for i, _ in enumerate(features[0]):
            x = [j[i] for j in features]
            x_values.append(x)


        t = tqdm(models)
        predictions = []
        for atom, model in enumerate(t):
            t.set_description(model.type)
            atom = atom % 3
            predictions.append(model.predict(x_values[atom]))
        
        return predictions

    def get_int_data(self, int_data_key):
        int_data = []

        if "IQA" in int_data_key.upper():
            attr = "IQA_terms"
            int_data_key = "E_IQA(A)"
        else:
            attr = "multipole_moments"
            int_data_key = int_data_key.lower()

        for point in self:
            point_data = [(key, val) for key, val in point.int.items()]
            point_data = UsefulTools.natural_sorted_tuple(point_data, 0)
            int_data.append([getattr(data, attr)[int_data_key] for atom, data in point_data])

        int_values = []
        for i, _ in enumerate(int_data[0]):
            val = [j[i] for j in int_data]
            int_values.append(val)
        
        return int_values

    def create_submission_script(self, type=None, name="SubmissionScript.sh", cores=1, submit=False, exit=True, sync=False):
        attributes = {
            "gaussian": "gjf",
            "aimall": "wfn",
            "ferebus": "training_set_directories"
        }

        self.submission_script = SubmissionScript(name, type=type)

        if type == "ferebus":
            for atom_directory in self.training_set_directories:
                self.submission_script.add_job(atom_directory)
            self.submission_script.add_option(option="-V")
        else:
            for point in self.points:
                job = getattr(point, attributes[type])
                self.submission_script.add_job(job.fname, options=job.output)

        self.submission_script.write_script()

        if submit:
            CSFTools.submit_scipt(self.submission_script.name, exit=exit, sync=sync)
    
    def get_wfn_energies(self):
        return [point.wfn.energy for point in self]

    def get_aimall_energeis(self):
        energies = []
        for point in self:
            energies.append([val.IQA_terms["E_IQA(A)"] for key, val in point.int.items()])
        return energies

    def get_atoms(self):
        return FileTools.natural_sort(list(self.points[0].int.keys()))

    def sort_by(self, attr, reverse=False):
        self.points.sort(key=lambda x: getattr(x, attr), reverse=reverse)
    
    def sort_by_name(self):
        self.points.sort(key=lambda x: x.name)

    def change_basis_set(self, basis_set, gen_basis_set=None):
        for point in self.points:
            point.gjf.basis_set = basis_set
            if basis_set.lower() == "gen":
                point.gjf.gen_basis_set = gen_basis_set

    def change_potential(self, potential):
        for point in self.points:
            point.gjf.potential = potential
   
    def set_charge(self, charge):
        for point in self.points:
            point.gjf.charge = charge

    def set_multiplicity(self, multiplicity):
        for point in self.points:
            point.gjf.multiplicity = multiplicity

    def add_keyword(self, keyword):
        for point in self.points:
            point.gjf.add_keyword(keyword)
 
    def add_keywords(self, keywords):
        for point in self:
            point.gjf.add_keywords(keywords)

    def write_gjfs(self):
        for point in self.points:
            point.gjf.write_gjf()
    
    def form_set(self, gjfs=[], wfns=[], int_directories=[]):
        global TRAINING_POINTS_TO_USE
        if self.training_set:
            gjf_len = min(len(gjfs), TRAINING_POINTS_TO_USE)
            wfn_len = min(len(wfns), TRAINING_POINTS_TO_USE)
            aim_len = min(len(int_directories), TRAINING_POINTS_TO_USE)
        else:
            gjf_len = wfn_len = aim_len = None
        for gjf, wfn, int_directory in itertools.zip_longest(gjfs[:gjf_len], wfns[:wfn_len], tqdm(int_directories[:aim_len])):
            self.add_point(gjf_file=gjf, wfn_file=wfn, int_directory=int_directory)
    
    def to_csv(self, fname, multipoles=True, iqa=True):
        for point in self:
            point.calculate_features()
        atoms = [x[0] for x in list(self[0].features.items())]
        for atom in atoms:
            nFeats = len(self[0].features[atom])
            with open(atom + "_" + fname, "w+") as f:
                title = "No." 
                for i in range(nFeats):
                    title += ",f%d" % (i+1)
                if multipoles:
                    moments_list = list(self[0].int[atom].multipole_moments.items())
                    for moment, _ in moments_list[:25]:
                        title += ",%s" % moment
                if iqa:
                    title += ",IQA"
                title += "\n"
                f.write(title)

                for i, point in enumerate(self):
                    line = str(i+1)
                    for feature in point.features[atom]:
                        line += ",%.10f" % feature
                    if multipoles:
                        moments_list = list(point.int[atom].multipole_moments.items())
                        for _, moment in moments_list[:25]:
                            line += ",%.12f" % moment
                    if iqa:
                        line += ",%.12f" % point.int[atom].IQA_terms["E_IQA(A)"]
                    line += "\n"
                    f.write(line)

        quit()

    #List Emulation Stuff
    def __len__(self):
        return len(self.points)
    
    def __getitem__(self, item):
        return self.points[item]
    
    def __delitem__(self, item):
        del self.points[item]
    
    def __iter__(self):
        return iter(self.points)
    
    def __contains__(self, value):
        return value in self.points


class GeometryData:

    def __init__(self, name, atoms, coordinates, calculate_features=True):
        self.name = name
        self.atoms = atoms
        self.coordinates = coordinates

        self.min_distance = math.inf
        self.cv_error = 0.0
        self.cv_atom = -1

        if calculate_features:
            self.features = calcFeats(ALF, coordinates)

    def get_atom_features(self, atom):
        return self.features[self.atoms.index(atom)]

    def set_cv_error(self, cv_error):
        self.cv_error = cv_error

    def get_distance_to(self, reference, atom=-1, theta=[]):
        feat_sum = 0.0
        for i in range(len(self.features)):
            for j in range(len(self.features[i])):
                if theta:
                    feat_sum += theta[i][j] * (self.features[i][j] - reference.features[i][j])**2
                else:
                    feat_sum += (self.features[i][j] - reference.features[i][j])**2
        if feat_sum < self.min_distance:
            self.min_distance = feat_sum
            self.cv_error = reference.cv_error
            self.cv_atom = atom


class Job:

    def __init__(self, job, options=[], type=None, ncores=2):
        self.type = type
        self.job = job
        self.options = [options] if isinstance(options, str) else options
        self.cores = ncores
        self.submission_string = self.get_submission_string()

    def get_submission_string(self):
        if self.type == "gaussian":
            return self.get_gaussian_submission_string()
        elif self.type == "aimall":
            return self.get_aimall_submission_string()
        elif self.type == "ferebus":
            return self.get_ferebus_submission_string()
        elif self.type == "python":
            return self.get_python_submission_string()
        elif self.type == "dlpoly":
            return self.get_dlpoly_submission_string()
        else:
            return self.get_default_submission_string()

    def get_gaussian_submission_string(self):
        return "export PREFERRED_SCDIR=/scratch\n" \
               "$g09root/g09/g09 %s %s\n" % (self.job, " ".join(self.options))

    def get_aimall_submission_string(self):
        global ENCOMP
        return "~/AIMAll/aimqb.ish " \
               "-nogui -usetwoe=0 -atom=all -encomp=%d -boaq=gs30 -iasmesh=fine -nproc=2 " \
               "%s >& %s\n" % (ENCOMP, self.job, " ".join(self.options))

    def get_ferebus_submission_string(self):
        global FILE_STRUCTURE
        global FEREBUS_VERSION

        if "fort" in FEREBUS_VERSION:
            ferebus_loc = FILE_STRUCTURE.get_file_path("programs") + "FEREBUS"
            copy_line = "cp %s %s\n" % (ferebus_loc, self.job)
            cd_line = "cd %s\n" % self.job
            while_loop = "while [ ! -f *q00* ]\n" \
                        "do\n" \
                        "export OMP_NUM_THREADS=$NSLOTS; ./FEREBUS\n" \
                        "done\n"
        elif "py" in FEREBUS_VERSION:
            ferebus_loc = FILE_STRUCTURE.get_file_path("programs") + "FEREBUS.py"
            copy_line = "cp %s %s\n" % (ferebus_loc, self.job)
            cd_line = "cd %s\n" % self.job
            while_loop = "python FEREBUS.py\n"
        return "%s%s%s" % (copy_line, cd_line, while_loop)

    def get_python_submission_string(self):
        return "python %s %s" % (self.job, " ".join(self.options))

    def get_dlpoly_submission_string(self):
        global FILE_STRUCTURE

        dlpoly_loc = FILE_STRUCTURE.get_file_path("programs") + "DLPOLY.Z"
        copy_line = "cp %s %s\n" % (dlpoly_loc, self.job)
        cd_line = "cd %s\n" % self.job
        exec_line = "./DLPOLY.Z\n"
        return "%s%s%s" % (copy_line, cd_line, exec_line)

    def get_default_submission_string(self):
        return "export $OMP_NUM_THREADS=%d; ./%s %s\n" % (self.cores, self.job, " ".join(self.options))


class SubmissionScript:

    def __init__(self, name, cores=1, type=None):
        self.name = self.check_name(name)
        self.type = type.lower()

        self.cores = cores
        self.options = {}
        self.modules = []
        self.jobs = []
        self.dir = None
        self.path = None

    def check_name(self, name):
        if not (name.endswith(".sh") or name.endswith(".sge")):
            return name + ".sh"
        else:
            return name

    def set_type(self, job_type):
        self.type = job_type

    def add_option(self, option=None, value=""):
        if option is not None:
            self.options[option] = value

    def add_module(self, module):
        if module not in self.modules:
            self.modules.append(module)

    def add_job(self, job, options=""):
        self.jobs.append(Job(job, options=options, type=self.type, ncores=self.cores))

    def change_directory(self, d):
        self.dir = d

    def set_cores(self, cores):
        self.cores = cores

    def set_default_cores(self):
        global GAUSSIAN_CORE_COUNT
        global AIMALL_CORE_COUNT
        global FEREBUS_CORE_COUNT
        global FEREBUS_VERSION

        if "py" in FEREBUS_VERSION:
            FEREBUS_CORE_COUNT = 1

        core_counts = {
            "gaussian": GAUSSIAN_CORE_COUNT,
            "aimall": AIMALL_CORE_COUNT,
            "ferebus": FEREBUS_CORE_COUNT
        }

        try:
            self.cores = core_counts[self.type]
        except:
            pass

    def add_path(self, path):
        self.path = path

    def get_cores_string(self):
        if self.cores == 1:
            return ""
        elif self.cores < 16:
            return "#$ -pe smp.pe %d\n" % self.cores

    def load_modules(self):
        global FEREBUS_VERSION

        gaussian_modules = ["apps/binapps/gaussian/g09d01_em64t"]

        if "fort" in FEREBUS_VERSION:
            ferebus_modules = ["mpi/intel-17.0/openmpi/3.1.3", "libs/intel/nag/fortran_mark26_intel"]
        elif "py" in FEREBUS_VERSION:
            ferebus_modules = ["apps/anaconda3/5.2.0/bin"]

        modules = {
            "gaussian": gaussian_modules,
            "ferebus": ferebus_modules
        }

        try:
            for module in modules[self.type]:
                self.add_module(module)
        except:
            pass

    def get_options_string(self):
        options_string = ""
        for key, val in self.options.items():
            options_string += "#$ %s %s\n" % (key, val)
        return options_string

    def get_modules_string(self):
        modules_string = ""
        for module in self.modules:
            modules_string += "module load %s\n" % module
        return modules_string

    def add_job_string(self, job_num, jobid):
        if jobid == 0:
            return self.jobs[job_num].submission_string
        else:
            job_string = "if [ \"$SGE_TASK_ID\" == \"%d\" ];\n" \
                         "then\n" \
                         "sleep 1\n" % jobid
            job_string += "%s" \
                          "fi\n\n" % self.jobs[job_num].submission_string
            return job_string

    def write_script(self):
        self.load_modules()
        self.set_default_cores()
        with open(self.name, "w+") as f:
            f.write("#!/bin/bash -l\n")
            f.write("#$ -cwd\n")
            f.write(self.get_cores_string())
            f.write(self.get_options_string())
            if len(self.jobs) > 1:
                f.write("#$ -t 1-%d\n" % len(self.jobs))
            f.write("\n")
            f.write(self.get_modules_string())
            f.write("\n")
            if self.path is not None:
                f.write("PATH=$PATH:%s\n\n" % self.path)
            if type(self.dir) == type(""):
                f.write("cd %s\n\n" % self.dir)

            number_of_jobs = len(self.jobs)
            if number_of_jobs == 1:
                f.write(self.add_job_string(0,0))
            elif number_of_jobs > 1:
                for i in range(number_of_jobs):
                    f.write(self.add_job_string(i, i+1))


class UsefulTools:

    @staticmethod
    def get_ichor_logo():
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
    def sorted_tuple(data, i, reverse=False):
        return sorted(data, key=lambda tup: tup[i], reverse=reverse)
    
    @staticmethod
    def natural_sorted_tuple(data, i):
        key = itemgetter(i)
        """ Sort the given iterable in the way that humans expect."""
        convert = lambda text: int(text) if text.isdigit() else text
        alphanum_key = lambda item: [convert(c) for c in re.findall('([0-9]+)', key(item))[-1]]
        return sorted(data, key = alphanum_key)

    @staticmethod
    def get_atoms(file=None):
        if not file:
            file = FileTools.get_files_in(FILE_STRUCTURE.get_file_path("ts_gjf"), "*.gjf")[0]

        coordinates = FileTools.get_coordinates(file)
        atoms = []
        for line in coordinates:
            atoms.append(line.split()[0])

        return atoms


class FileTools:

    @staticmethod
    def setup_file_structure():
        tree = Tree()

        tree.create_node("ICHOR", "file_locs")

        tree.create_node("TRAINING_SET", "training_set", parent="file_locs")
        tree.create_node("GJF", "ts_gjf", parent="training_set")
        tree.create_node("WFN", "ts_wfn", parent="training_set")
        tree.create_node("AIMALL", "ts_aimall", parent="training_set")
        tree.create_node("FEREBUS", "ts_ferebus", parent="training_set")
        tree.create_node("MODELS", "ts_models", parent="training_set")

        tree.create_node("SAMPLE_POOL", "sample_pool", parent="file_locs")
        tree.create_node("GJF", "sp_gjf", parent="sample_pool")
        tree.create_node("WFN", "sp_wfn", parent="sample_pool")
        tree.create_node("AIMALL", "sp_aimall", parent="sample_pool")

        tree.create_node("TEST_SET", "test_set", parent="file_locs")
        tree.create_node("GJF", "sp_gjf", parent="test_set")
        tree.create_node("WFN", "sp_wfn", parent="test_set")
        tree.create_node("AIMALL", "sp_aimall", parent="test_set")

        tree.create_node("DLPOLY", "dlpoly", parent="file_locs")

        tree.create_node("LOG", "log", parent="file_locs")

        tree.create_node("PROGRAMS", "programs", parent="file_locs")

        tree.create_node("OPT", "opt", parent="file_locs")

        tree.create_node("TEMP", "temp", parent="file_locs")

        return tree

    @staticmethod
    def setup_important_files():
        global FILE_STRUCTURE

        files = {}
        files["sp_aimall_energies"] = FILE_STRUCTURE.get_file_path("sp_aimall") + "AIMALL_Energies.csv"

        return files

    @staticmethod
    def get_files_in(d, filetype, sorting="normal"):
        if not d.endswith("/"):
            d += "/"
        if sorting == "normal":
            return sorted(glob(d + filetype))
        elif sorting == "natural":
            return FileTools.natural_sort(glob(d + filetype))
        else:
            return glob(d + filetype)

    @staticmethod
    def natural_sort(l):
        convert = lambda text: int(text) if text.isdigit() else text
        alphanum_key = lambda key: [convert(c) for c in re.findall('([0-9]+)', key)[-1]]
        return sorted(l, key=alphanum_key)

    @staticmethod
    def get_coordinates(fname):
        coordinates = []
        with open(fname, "r") as f:
            for line in f:
                if re.match("\s*\w+\s+([+-]?\d+.\d+([Ee]?[+-]?\d+)?\s*){3}", line):
                    coordinates.append(line)
                elif coordinates:
                    break
        return coordinates

    @staticmethod
    def parse_coordinate_lines(lines):
        coordinates = []
        atoms = []
        for line in lines:
            line_split = line.split()
            atoms.append(line_split[0])
            coordinates.append([line_split[1], line_split[2], line_split[3]])

        return atoms, coordinates

    @staticmethod
    def get_last_coordinates(fname):
        coordinates = []
        for line in reversed(list(open(fname))):
            if re.match("\s*\w+\s+([+-]?\d+.\d+([Ee]?[+-]?\d+)?\s*){3}", line):
                coordinates.append(line)
            elif coordinates:
                break
        return list(reversed(coordinates))

    @staticmethod
    def remove_files(directory, fileType):
        if not fileType.startswith("."):
            filetype = "." + fileType
        directory_list = os.listdir(directory)
        for item in directory_list:
            if item.endswith(fileType):
                os.remove(os.path.join(directory, item))

    @staticmethod
    def add_functional(wfn_location, functional):
        wfns = FileTools.get_files_in(wfn_location, "*.wfn")
        for wfn in wfns:
            with open(wfn, "r") as f:
                lines = f.readlines()
            if functional not in lines[1]:
                lines[1] =  "%s   %s\n" % (lines[1].strip(),functional)
            with open(wfn, "w") as f:
                f.writelines(lines)

    @staticmethod
    def remove_directory(directory):
        if os.path.isdir(directory):
            shutil.rmtree(directory)

    @staticmethod
    def make_directory(directory):
        if not os.path.isdir(directory):
            os.mkdir(directory)

    @staticmethod
    def make_clean_directory(directory):
        if not os.path.isdir(directory):
            os.mkdir(directory)
        else:
            for item in os.listdir(directory):
                if os.path.isdir(os.path.join(directory, item)):
                    shutil.rmtree(os.path.join(directory, item))
                else:
                    os.unlink(os.path.join(directory, item))

    @staticmethod
    def copy_file(src, dst):
        shutil.copy2(src, dst)

    @staticmethod
    def copy_files(src, dst, fileType):
        if not fileType.startswith("."):
            filetype = "." + fileType
        for item in os.listdir(src):
            if item.endswith(fileType):
                pathname = os.path.join(src, item)
                if os.path.isfile(pathname):
                    shutil.copy2(pathname, dst)

    @staticmethod
    def move_file(src, dst):
        if os.path.isfile(dst):
            os.remove(dst)
        shutil.move(src, dst)

    @staticmethod
    def move_files(src, dst, fileType):
        if not fileType.startswith("."):
            filetype = "." + fileType
        for item in os.listdir(src):
            if item.endswith(fileType):
                pathname = os.path.join(src, item)
                destination = os.path.join(dst, item)
                if os.path.isfile(pathname):
                    FileTools.move_file(pathname, destination)

    @staticmethod
    def move_directory(src, dst):
        shutil.move(src, dst)
        
    @staticmethod
    def move_directories(src, dst, pattern):
        pattern = pattern.replace("*", "")
        d = src
        directories = FileTools.get_directories(src)
        for directory in directories:
            if directory.endswith("/"):
                directory = directory.rstrip("/")
            d, name = os.path.split(directory)
            if pattern in name:
                FileTools.move_directory(directory, os.path.join(dst, name))
    
    @staticmethod
    def get_num(f):
        if f.endswith("/"):
            f = f [:-1]
        fname = os.path.basename(f)
        num_str = re.findall("\d+", fname)[0]
        return int(num_str)

    @staticmethod
    def increment_files(files, increment, move_files=True):
        for i, f in enumerate(files):
            try:
                if f.endswith("/"):
                        f = f [:-1]
                d = os.path.dirname(f)
                fname = os.path.basename(f)
                num_str = re.findall("\d+", fname)[0]
                num = int(num_str) + increment
                new_f = os.path.join(d, fname.replace(num_str, str(num).zfill(len(num_str))))
                if move_files:
                    FileTools.move_file(f, new_f)
                files[i] = new_f
            except:
                print("Cannot increment file: {}".format(f))
        return files

    @staticmethod
    def get_fname_base(f):
        fname = os.path.basename(f)
        base = fname.split(".")[0]
        return fname, base

    @staticmethod
    def update_file(oldf, newf):
        newfname, newbase = self.get_fname_base(newf)
        oldfname, oldbase = self.get_fname_base(oldf)

        with open(oldf, "r") as f:
            data = f.readlines()
        
        with open(oldf, "w") as f:
            for i, line in enumerate(data):
                if oldf in line:
                    data[i] = line.replace(oldf, newf)
                elif oldfname in line:
                    data[i] = line.replace(oldfname, newfname)
                elif oldbase in line:
                    data[i] = line.replace(oldbase, newbase)

    @staticmethod
    def get_directories(directory):
        directories = []
        for item in os.listdir(directory):
            if os.path.isdir(os.path.join(directory, item)):
                directories.append(os.path.join(directory, item))
        return directories

    @staticmethod
    def get_atom_directories(directory):
        directories = []
        for item in os.listdir(directory):
            if os.path.isdir(os.path.join(directory, item)):
                if re.match("\A\w{1,2}\d+(_\w{1,2}\d+)?$", item):
                    directories.append(os.path.join(directory, item))
        return directories

    @staticmethod
    def get_base(fname):
        if fname.endswith("/"):
            fname = fname.rstrip("/")
        return os.path.split(fname)[1].split(".")[0].split("_")[0]

    @staticmethod
    def cleanup_aimall_dir(aimall_dir, split_into_atoms=False, remove_wfns=True):
        all_directories = FileTools.get_directories(aimall_dir)

        if split_into_atoms:
            atom_directories = FileTools.get_atom_directories(aimall_dir)
            look_through_directories = sorted([x for x in all_directories if x not in atom_directories])

            if len(atom_directories) == 0:
                example_directory = look_through_directories[0]
                int_files = FileTools.get_files_in(example_directory, "*.int")
                for int_file in int_files:
                    filename = int_file.split("/")[-1]
                    os.mkdir(aimall_dir + filename.replace(".int", "").upper())

            for directory in look_through_directories:
                if re.match("\S+_atomicfiles", directory):
                    current_system = directory.split("/")[-1]
                    int_files = FileTools.get_files_in(directory, "*.int")

                    for int_file in int_files:
                        intFileName = int_file.split("/")[-1]
                        atom = intFileName.replace(".int", "")
                        newFileName = aimall_dir + atom.upper() + "/" + current_system.replace("_atomicfiles", "") \
                                      + "_" + atom + ".int"
                        shutil.move(int_file, newFileName)

                    FileTools.remove_directory(directory)
        else:
            for directory in all_directories:
                if re.match("\S+_atomicfiles", directory):
                    int_files = FileTools.get_files_in(directory, "*.int")
                    directory_base = directory.split("/")[-1].replace("_atomicfiles", "")
                    for int_file in int_files:
                        int_base = os.path.split(int_file)[1].split(".")[0]
                        if not int_base.startswith(directory_base):
                            new_int_file = "%s/%s_%s.int" % (directory, directory_base, int_base)
                            FileTools.move_file(int_file, new_int_file)
                    FileTools.remove_files(directory, ".inp")

        FileTools.remove_files(aimall_dir, ".extout")
        FileTools.remove_files(aimall_dir, ".mgp")
        FileTools.remove_files(aimall_dir, ".mgpviz")
        FileTools.remove_files(aimall_dir, ".sum")
        FileTools.remove_files(aimall_dir, ".sumviz")
        if remove_wfns:
            FileTools.remove_files(aimall_dir, ".wfn")
        FileTools.remove_files(aimall_dir, ".log")

    @staticmethod
    def remove_no_noise(model):
        with open(model, "r") as f:
            data = f.readlines()

        del data[6]

        with open(model, "w") as f:
            f.writelines(data)


class ReadFiles:

    @staticmethod
    def GJFs(gjfs):
        gjf_data = []
        #gjf_files = FileTools.get_files_in(gjf_dir, "*.gjf")
        for gjf in gjfs:
            gjf_name = gjf.split("/")[-1].replace(".gjf", "")
            gjf_coordinates, atoms = [], []

            atom_counter = 1
            coordinates = FileTools.get_coordinates(gjf)
            for coordinate in coordinates:
                coordinate_split = coordinate.split()
                atom = coordinate_split[0] + str(atom_counter)
                atom_coordinates = []
                for i in range(1, 4):
                    atom_coordinates.append(float(coordinate_split[i]))
                atoms.append(atom)
                gjf_coordinates.append(atom_coordinates)
                atom_counter += 1

            gjf_data.append(GeometryData(gjf_name, atoms, gjf_coordinates))
        
        return gjf_data

    # @staticmethod
    # def Ints(ints):


class CSFTools:

    @staticmethod
    def submit_scipt(script, hold_jid=None, sync=False, exit=False, return_jid=False):
        """
            :param script: fname of script e.g 'GaussSub.sh'
            :param hold_jid: jid to hold for if applicable
            :param sync: whether to submit the script to run in the background or wait for the job to finish
            :param exit: boolean to tell script to exit after submistting script
            :return: None submits script provided

            Notes
            -----
            Needs refactoring
        """
        if sync:
            job = Popen(["qsub", "-sync", "y", script])
            job.communicate()
        else:
            if return_jid:
                if not hold_jid:
                    cmd = ['qsub ' + script]
                else:
                    cmd = ['qsub -hold_jid ' + hold_jid + ' ' + script]
                result = str(subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)).lstrip("b")
                result = result.split()[2]
                if "." in result:
                    result = result.split(".")[0]
                return result
            else:
                if hold_jid is not None:
                    os.system("qsub %s %s %s" % ("-hold_jid", hold_jid, script))
                else:
                    os.system("qsub %s" % script)

        if exit:
            sys.exit(0)

    @staticmethod
    def del_jobs():
        with open("jid.txt", "r") as f:
            jobs = f.readlines()

        for job in reversed(jobs):
            os.system("qdel %s" % job.strip())


class FerebusTools:

    @staticmethod
    def write_finput(directory: str, natoms: int, atom: str, training_set_size: int,
                     predictions: int = 0, nproperties: int = 6, optimization: int = "pso") -> None:
        global SYSTEM_NAME
        global KERNEL
        global FEREBUS_VERSION

        if not directory.endswith("/"):
            directory += "/"

        atom_num = re.findall("\d+", atom)[0]

        with open(directory + "FINPUT.txt", "w+") as finput:
            finput.write("%s\n" % SYSTEM_NAME)
            finput.write("natoms %d\n" %natoms)
            finput.write("starting_properties 1 \n")
            finput.write("nproperties %d\n" % nproperties)
            finput.write("#\n# Training set size and definition of reduced training set size\n#\n")
            finput.write("full_training_set %d\n" % training_set_size)
            finput.write("#\n# Prediction number and definition of new predictions\n#\n")
            finput.write("predictions %d\n" % predictions)
            if "py" in FEREBUS_VERSION:
                finput.write("kernel %s\n" % KERNEL)
            finput.write(
                "#\nfeatures_number 0        # if your are kriging only one atom or you don't want to use he standard "
                "calculation of the number of features based on DOF of your system. Leave 0 otherwise\n#\n")
            finput.write("#\n#%s\n" % ("~" * 97))

            finput.write("# Optimizers parameters\n#\n")
            finput.write("redo_weights n\n")
            finput.write("dynamical_selection n\n")
            finput.write("optimization %s          "
                         "# choose between DE (Differential Evolution) "
                         "and PSO (Particle Swarm Optimization)\n" % optimization)
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
            finput.write("#\n#%s\n" % ("~" * 97))

            finput.write("# PSO Specific keywords\n#\n")
            finput.write("swarm_specifier  D       "
                         "# answer dynamic (D) or static "
                         "(S) as option for swarm optimization\n")
            finput.write("swarm_pop        1440       "
                         "# if swarm opt is set as 'static' the number of particle must be specified\n")
            finput.write("cognitive_learning   1.49400\n")
            finput.write("inertia_weight   0.72900\n")
            finput.write("social_learning   1.49400\n")
            finput.write("#\n#%s\n" % ("~" * 97))

            finput.write("# DE Specific keyword\n#\n")
            finput.write("population_size 8\n")
            finput.write("mutation_strategy 4\n")
            finput.write("population_reduction n\n")
            finput.write("reduction_start 5        # the ratio convergence/reduction_start < 5\n")
            finput.write("#\n#%s\n" % ("~" * 97))

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
            finput.write("#\n#%s\n" % ("~" * 97))

            finput.write("# Atoms type and index\n#\n")
            finput.write("atoms                      "
                         "# this keyword tells the program than the next lines are the index number and atom type\n")
            finput.write("%s   %s\n" % (atom_num, atom))


class DLPOLYsetup:

    def __init__(self, directory,  atoms, number_of_training_points, write_setup_files=True):
        self.directory = directory
        self.atoms = atoms
        self.number_of_training_points = number_of_training_points

        global DLPOLY_NUMBER_OF_STEPS
        global DLPOLY_TIMESTEP
        global DLPOLY_TEMPERATURE
        global DLPOLY_PRINT_EVERY

        self.number_of_steps = DLPOLY_NUMBER_OF_STEPS
        self.timestep = DLPOLY_TIMESTEP
        self.temperature = float(DLPOLY_TEMPERATURE)
        self.print_every = DLPOLY_PRINT_EVERY

        if not self.directory.endswith("/"):
            self.directory += "/"

        if write_setup_files:
            self.writeCONTROL()
            self.writeFIELD()
            self.writeKRIGING()

    def writeCONTROL(self):
        global SYSTEM_NAME
        global KERNEL

        with open(self.directory + "CONTROL", "w+") as o:
            o.write("Title: %s\n" % SYSTEM_NAME)
            o.write("# This is a generic CONTROL file. Please adjust to your requirement.\n")
            o.write("# Directives which are commented are some useful options.\n\n")
            o.write("ensemble nvt hoover 0.02\n")
            if self.temperature == 0:
                o.write("temperature 10.0\n\n")
            else:
                o.write("temperature %.1f\n\n" % self.temperature)
            if self.temperature == 0:
                o.write("#perform zero temperature run (really set to 10K)\n")
                o.write("zero\n")
            # o.write("# optimise distance 0.000001\n\n")
            o.write("# Cap forces during equilibration, in unit kT/angstrom.\n")
            o.write("# (useful if your system is far from equilibrium)\n")
            o.write("cap 100.0\n\n")
            # o.write("# Increase array size per domain\n")
            # o.write("# densvar 10 %\n\n")
            # o.write("# Bypass checking restrictions and reporting\n")
            # o.write("#no index\n")
            # o.write("#no strict\n")
            # o.write("#no topolgy\n")
            o.write("no vdw\n\n")
            o.write("steps %d\n" % self.number_of_steps)
            o.write("equilibration %d\n" % self.number_of_steps)
            # o.write("#scale every 2\n")
            o.write("timestep %f\n" % self.timestep)
            o.write("cutoff 15.0\n")
            o.write("fflux\n\n")
            if KERNEL != "rbf":
                o.write("fflux_kernel %s" % KERNEL)
            # o.write("# Need these for bond contraints\n")
            # o.write("#mxshak 100\n")
            # o.write("#shake 1.0e-6\n\n")
            o.write("# Continue MD simulation\n")
            # o.write("#restart\n\n")
            o.write("traj 0 1 2\n")
            o.write("print every %d\n" % self.print_every)
            o.write("stats every %d\n" % self.print_every)
            o.write("job time 10000000\n")
            o.write("close time 20000\n")
            o.write("finish")

    def writeKRIGING(self):
        global SYSTEM_NAME
        global ALF

        with open(self.directory + "KRIGING.txt", "w+") as o:
            o.write("%s\t\t#prefix of model file names for the considered system\n" % SYSTEM_NAME)
            o.write("%d\t\t#number of atoms in the kriged system\n" % len(self.atoms))
            o.write("3\t\t#number of moments (first 3 are to be IQA energy components xc slf src)\n")
            o.write("%d\t\t#max number of training examples\n" % self.number_of_training_points)
            for i in range(len(self.atoms)):
                o.write("%s %d %d %d" % (self.atoms[i], ALF[i][0] + 1, ALF[i][1] + 1, ALF[i][2] + 1))
                for j in range(len(self.atoms)):
                    if i == j:
                        o.write(" 0")
                    else:
                        o.write(" %d" % (j + 1))
                o.write("\n")

    def writeFIELD(self):
        global SYSTEM_NAME

        weight_dict = {"H": 1.007975, "HE": 4.002602, "LI": 6.9675, "BE": 9.0121831, "B": 10.8135, "C": 12.0106,
                       "N": 14.006855, "O": 15.9994, "F": 18.99840316, "NE": 20.1797, "NA": 22.98976928, "MG": 24.3055,
                       "AL": 26.9815385, "SI": 28.085, "P": 30.973762, "S": 32.0675, "CL": 35.4515, "AR": 39.948,
                       "K": 39.0983, "CA": 40.078, "SC": 44.955908, "TI": 47.867, "V": 50.9415, "CR": 51.9961,
                       "MN": 54.938044, "FE": 55.845, "CO": 58.933194, "NI": 58.6934, "CU": 63.546, "ZN": 65.38,
                       "GA": 69.723, "GE": 72.63, "AS": 74.921595, "SE": 78.971, "BR": 79.904, "KR": 83.798,
                       "RB": 85.4678,
                       "SR": 87.62, "Y": 88.90584, "ZR": 91.224, "NB": 92.90637, "MO": 95.95}

        with open(self.directory + "FIELD", "w+") as o:
            o.write("DL_FIELD v3.00\nUnits internal\nMolecular types 1\n")
            o.write("Molecule name %s\n" % SYSTEM_NAME)
            o.write("nummols 1\n")
            o.write("atoms %d\n" % len(self.atoms))
            for atom in self.atoms:
                o.write(atom + "\t\t" + "%.7s" % str(weight_dict[atom]) + "     0.0   1   0\n")
            o.write("finish\nclose")

    def write_gjf_to_config(self, gjf_fname):
        coordinates = FileTools.get_coordinates(gjf_fname)

        config_fname = self.directory + "CONFIG"

        with open(config_fname, "w+") as f:
            f.write("dlp config file converted from gjf\n")
            f.write("\t0\t0\n")
            atom_count = 1
            for line in coordinates:
                line_split = line.split()
                f.write("%s %d\n" % (line_split[0], atom_count))
                f.write("%s\t\t%s\t\t%s\n" % (line_split[1], line_split[2], line_split[3]))
                atom_count += 1


def AtomicLocalFrame(fname):
    """

    A function that takes a gjf file and returns the Atomic Local Frame (ALF) of the configuration in the file

    Parameters
    ----------
    fname : String
         The gjf file name you would like to determine the alf from

    Returns
    -------
    float[natoms][3]
        A 2D array of type float with

    Notes
    -----
    --> Would like to include more files than GJF (eg .xyz)

    """

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

    atoms = []
    connectivity = []

    class ALFAtom:
        global type2mass
        global type2rad

        def __init__(self, a, c, num):
            self.type = a
            self.coordinates = c
            self.mass = type2mass[self.type]
            self.rad = type2rad[self.type]
            self.number = num
            self.bonds = []

        def set_bonds(self, bond_list):
            self.bonds = bond_list

    def get_coords(fin):
        n = 1
        with open(fin, "r") as f:
            for line in f:
                if re.match("\s*\w+\s+([+-]?\d+.\d+){3}", line):
                    l = line.split()
                    atoms.append(ALFAtom(l[0], [float(l[1]), float(l[2]), float(l[3])], n))
                    n += 1

    def get_dist(a, b):
        s = 0
        for i in range(len(a)):
            s += (a[i]-b[i])**2
        return math.sqrt(s)

    def get_connectivity():
        global connectivity
        connectivity = [[0 for x in range(len(atoms))] for y in range(len(atoms))]

        for i in range(len(atoms)):
            for j in range(len(atoms)):
                if i == j:
                    continue
                else:
                    v1 = atoms[i].coordinates
                    v2 = atoms[j].coordinates

                    max_dist = 1.2 * (atoms[i].rad + atoms[j].rad)
                    euc_dist = get_dist(v1, v2)

                    if euc_dist < max_dist:
                        connectivity[i][j] = 1

    def setup_bonds():
        global connectivity
        for iatom in range(len(atoms)):
            atoms[iatom].set_bonds([(i+1) for i, j in enumerate(connectivity[iatom]) if j == 1])

    def get_sum(base_atom, atom, levels):
        i = 0
        total_mass = atoms[atom-1].mass
        bonds = atoms[atom-1].bonds
        atoms_searched = [base_atom, atom]
        while i < levels:
            bonds_backup = list(bonds)
            bonds = list(set(bonds) - set(atoms_searched))
            for iatom in bonds:
                atoms_searched.append(iatom)
                total_mass += atoms[iatom-1].mass

            bonds = []
            for bond in bonds_backup:
                bonds += atoms[bond-1].bonds
                bonds = list(set(bonds) - set(atoms_searched))

            if len(bonds) == 0:
                return -1
            else:
                i+=1
        return total_mass

    def detALF():
        alf = []
        for iatom in range(len(atoms)):
            bond_list = atoms[iatom].bonds

            atom_alf = [iatom+1]

            for alf_axis in range(2):
                largest_mass = -1
                queue = []

                for bond in bond_list:
                    mass = atoms[bond-1].mass
                    if mass > largest_mass:
                        largest_mass = mass
                        queue = []
                        queue.append(atoms[bond-1].number)
                    elif mass == largest_mass:
                        queue.append(atoms[bond-1].number)

                if len(queue) == 1:
                    atom_alf.append(queue[0])
                else:
                    symm_check = []
                    for atom in list(queue):
                        symm_check.append(atoms[atom-1].bonds)
                    symm_check = symm_check.count(symm_check[0]) == len(symm_check)
                    if not symm_check:
                        conflict = True
                        level = 1
                        while conflict:
                            atom_list = list(queue)
                            priority = list()

                            for atom in queue:
                                priority.append(get_sum(iatom+1, atom, level))

                            highest_priority = -2
                            for j in range(len(priority)):
                                if priority[j] > highest_priority:
                                    highest_priority = priority[j]
                                    queue = list()
                                    queue.append(atom_list[j])
                                elif priority[j] == highest_priority:
                                    queue.append(atom_list[j])

                            if highest_priority == -1:
                                conflict = False
                            elif len(queue) > 1:
                                level += 1
                            else:
                                conflict = False
                    atom_alf.append(queue[0])

                if len(bond_list) == 1:
                    base_atom = bond_list[0]
                    for bond in atoms[base_atom-1].bonds:
                        bond_list.append(bond)

                bond_list = list(set(bond_list) - set(atom_alf))

            alf.append(atom_alf)
        return alf

    get_coords(fname)
    get_connectivity()
    setup_bonds()

    return detALF()


def calcFeats(alf, coordinates):
    #ang2bohr = 1.889725989
    ang2bohr = 1.88971616463
    # ang2bohr = 1.0

    def C_1k(coordinates, alf, atm, feature, k):
        # dim: x = 0, y = 1, z = 2
        xx1 = (coordinates[alf[atm][1]][0] - coordinates[atm][0]) / feature
        yy1 = (coordinates[alf[atm][1]][1] - coordinates[atm][1]) / feature
        zz1 = (coordinates[alf[atm][1]][2] - coordinates[atm][2]) / feature

        c_1k = [xx1, yy1, zz1]

        if k >= 0:
            return c_1k[k]
        else:
            return c_1k

    def C_2k(coordinates, alf, atm, k):
        xdiff1 = coordinates[alf[atm][1]][0] - coordinates[atm][0]
        ydiff1 = coordinates[alf[atm][1]][1] - coordinates[atm][1]
        zdiff1 = coordinates[alf[atm][1]][2] - coordinates[atm][2]

        xdiff2 = coordinates[alf[atm][2]][0] - coordinates[atm][0]
        ydiff2 = coordinates[alf[atm][2]][1] - coordinates[atm][1]
        zdiff2 = coordinates[alf[atm][2]][2] - coordinates[atm][2]

        sigma_fflux = -(xdiff1 * xdiff2 + ydiff1 * ydiff2 + zdiff1 * zdiff2) / (
                xdiff1 * xdiff1 + ydiff1 * ydiff1 + zdiff1 * zdiff1)

        y_vec1 = sigma_fflux * xdiff1 + xdiff2
        y_vec2 = sigma_fflux * ydiff1 + ydiff2
        y_vec3 = sigma_fflux * zdiff1 + zdiff2

        yy = math.sqrt(y_vec1 * y_vec1 + y_vec2 * y_vec2 + y_vec3 * y_vec3)

        y_vec1 /= yy
        y_vec2 /= yy
        y_vec3 /= yy

        c_2k = [y_vec1, y_vec2, y_vec3]

        if k >= 0:
            return c_2k[k]
        else:
            return c_2k

    def C_3k(coordinates, alf, atm, feature):
        xx3 = C_1k(coordinates, alf, atm, feature, 1) * C_2k(coordinates, alf, atm, 2) - C_1k(coordinates, alf, atm,
                                                                                              feature, 2) * C_2k(
            coordinates, alf, atm, 1)
        yy3 = C_1k(coordinates, alf, atm, feature, 2) * C_2k(coordinates, alf, atm, 0) - C_1k(coordinates, alf, atm,
                                                                                              feature, 0) * C_2k(
            coordinates, alf, atm, 2)
        zz3 = C_1k(coordinates, alf, atm, feature, 0) * C_2k(coordinates, alf, atm, 1) - C_1k(coordinates, alf, atm,
                                                                                              feature, 1) * C_2k(
            coordinates, alf, atm, 0)

        c_3k = [xx3, yy3, zz3]

        return c_3k

    features = []
    for iatm in range(len(coordinates)):
        atom_features = []

        xdiff1 = coordinates[alf[iatm][1]][0] - coordinates[iatm][0]
        ydiff1 = coordinates[alf[iatm][1]][1] - coordinates[iatm][1]
        zdiff1 = coordinates[alf[iatm][1]][2] - coordinates[iatm][2]

        # Calculate Bond 1 (convert to Bohr)
        bond_1 = math.sqrt(xdiff1 * xdiff1 + ydiff1 * ydiff1 + zdiff1 * zdiff1)
        atom_features.append(bond_1 * ang2bohr)

        xdiff2 = coordinates[alf[iatm][2]][0] - coordinates[iatm][0]
        ydiff2 = coordinates[alf[iatm][2]][1] - coordinates[iatm][1]
        zdiff2 = coordinates[alf[iatm][2]][2] - coordinates[iatm][2]

        # Calculate Bond 2 (convert to Bohr)
        bond_2 = math.sqrt(xdiff2 * xdiff2 + ydiff2 * ydiff2 + zdiff2 * zdiff2)
        atom_features.append(bond_2 * ang2bohr)

        # Calculate Angle 1 (Chi)
        temp = xdiff1 * xdiff2 + ydiff1 * ydiff2 + zdiff1 * zdiff2

        chi_1 = math.acos(temp / (bond_1 * bond_2))
        atom_features.append(chi_1)

        for j in range(len(coordinates)):
            if not ((j == iatm) or (j == alf[iatm][1]) or (j == alf[iatm][2])):
                xdiff = coordinates[j][0] - coordinates[iatm][0]
                ydiff = coordinates[j][1] - coordinates[iatm][1]
                zdiff = coordinates[j][2] - coordinates[iatm][2]

                lxx = C_1k(coordinates, alf, iatm, bond_1, -1)
                lyy = C_2k(coordinates, alf, iatm, -1)
                lzz = C_3k(coordinates, alf, iatm, bond_1)

                # Calculate Bond n (convert to Bohr)
                bond_n = math.sqrt(pow(xdiff, 2) + pow(ydiff, 2) + pow(zdiff, 2))
                atom_features.append(bond_n * ang2bohr)

                # Calculate Theta n
                zeta3 = lzz[0] * xdiff + lzz[1] * ydiff + lzz[2] * zdiff
                theta_n = math.acos(zeta3 / bond_n)
                atom_features.append(theta_n)

                # Calculate Phi n
                zeta2 = lyy[0] * xdiff + lyy[1] * ydiff + lyy[2] * zdiff
                zeta1 = lxx[0] * xdiff + lxx[1] * ydiff + lxx[2] * zdiff
                phi_n = math.atan2(zeta2, zeta1)
                atom_features.append(phi_n)

        features.append(atom_features)

    return features


def defineGlobals():
    global FILE_STRUCTURE
    global IMPORTANT_FILES
    global CONFIG

    global SYSTEM_NAME
    global ALF
    global MAX_ITERATION
    global POINTS_PER_ITERATION

    global MULTIPLE_ADDITION_MODE

    global POTENTIAL
    global BASIS_SET

    global ENCOMP

    global KERNEL
    global FEREBUS_VERSION

    global GAUSSIAN_CORE_COUNT
    global AIMALL_CORE_COUNT
    global FEREBUS_CORE_COUNT

    global DLPOLY_NUMBER_OF_STEPS
    global DLPOLY_TIMESTEP
    global DLPOLY_TEMPERATURE
    global DLPOLY_PRINT_EVERY

    global PREDICTION_MODE
    global NORMALIZE

    global PRECALCULATE_AIMALL

    FILE_STRUCTURE = FileTools.setup_file_structure()
    IMPORTANT_FILES = FileTools.setup_important_files()

    alf_reference_file = None

    # config reading
    config = ConfigProvider()
    CONFIG = config

    for key, val in config.items():
        if key == "SYSTEM_NAME":
            SYSTEM_NAME = val

        if key == "ALF":
            ALF = ast.literal_eval(val)
        if key == "ALF_REFERENCE_FILE":
            alf_reference_file = val

        if key == "POINTS_PER_ITERATION":
            POINTS_PER_ITERATION = int(val)
        if key == "MAX_ITERATION":
            MAX_ITERATION = int(val)
        if key == "MULTIPLE_ADDITION_MODE":
            MULTIPLE_ADDITION_MODE = val

        if key == "POTENTIAL":
            POTENTIAL = val.upper()
        if key == "BASIS_SET":
            BASIS_SET = val
        
        if key == "ENCOMP":
            ENCOMP = int(val)
        
        if key == "KERNEL":
            KERNEL = val.lower()
        if key == "FEREBUS_VERSION":
            FEREBUS_VERSION = val.lower()

        if key == "PREDICTION_MODE":
            PREDICTION_MODE = val.lower()
        if key == "NORMALIZE":
            NORMALIZE = bool(val)

        if key == "GAUSSIAN_CORE_COUNT":
            GAUSSIAN_CORE_COUNT = int(val)
        if key == "AIMALL_CORE_COUNT":
            AIMALL_CORE_COUNT = int(val)
        if key == "FEREBUS_CORE_COUNT":
            FEREBUS_CORE_COUNT = int(val)
        if key == "DLPOLY_CORE_COUNT":
            DLPOLY_CORE_COUNT = int(val)

        if key == "DLPOLY_NUMBER_OF_STEPS":
            DLPOLY_NUMBER_OF_STEPS = int(val)
        if key == "DLPOLY_TIMESTEP":
            DLPOLY_TIMESTEP = float(val)
        if key == "DLPOLY_TEMPERATURE":
            DLPOLY_TEMPERATURE = int(val)
        if key == "DLPOLY_PRINT_EVERY":
            DLPOLY_PRINT_EVERY = int(val)

        if key == "PRECALCULATE_AIMALL":
            PRECALCULATE_AIMALL = val.lower() in ['true', '1', 't', 'y', 'yes', 'yeah']

    # ALF checking
    if not ALF:
        if not alf_reference_file:
            try:
                alf_reference_file = FileTools.get_files_in(FILE_STRUCTURE.get_file_path("ts_gjf"), "*.gjf")[0]
            except:
                try:
                    alf_reference_file = FileTools.get_files_in(FILE_STRUCTURE.get_file_path("sp_gjf"), "*.gjf")[0]
                except:
                    print("\nCould not find a reference gjf to determine the ALF")
                    print("Please specify reference file or define explicitly")
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

    parser = ArgumentParser(description="ICHOR: A kriging training suite")

    parser.add_argument("-a", "--auto", dest="auto_sub", action="store_true",
                        help="Run ICHOR in Auto Submission Mode")

    parser.add_argument("-i", "--iteration", dest="iteration", type=int, metavar='N',
                        help="Current iteration during Auto Submission Mode")

    parser.add_argument("-s", "--step", dest="step", type=int, metavar='N',
                        help="Current ICHOR step during Auto Submission Mode")

    args = parser.parse_args()
    argsdict = vars(args)

    if argsdict['auto_sub']:
        AUTO_SUBMISSION_MODE = True

        if argsdict['iteration']:
            ITERATION = int(argsdict['iteration'])

        if argsdict['step']:
            STEP = int(argsdict['step'])


def createGaussScript(dir, name="GaussSub.sh", files=None):
    global MACHINE
    global GAUSSIAN_CORE_COUNT

    if not files:
        gjfs = FileTools.get_files_in(dir, "*.gjf")
    else:
        gjfs = files
    gaussSub = SubmissionScript(name, type="gaussian", cores=GAUSSIAN_CORE_COUNT)
    if MACHINE == "csf2":
        gaussSub.add_module("apps/binapps/gaussian/g09b01_em64t")
    if MACHINE == "csf3":
        gaussSub.add_module("apps/binapps/gaussian/g09d01_em64t")
    # gaussSub.change_directory(dir)
    for gjf in gjfs:
        gaussSub.add_job(gjf, options=gjf.replace(".gjf", ".log"))
    gaussSub.write_script()


def createAimScript(dir, name="AIMSub.sh", files=None):
    global AIMALL_CORE_COUNT

    if not files:
        wfns = FileTools.get_files_in(dir, "*.wfn")
    else:
        wfns = files

    aimsub = SubmissionScript(name, type="aimall", cores=AIMALL_CORE_COUNT)

    aimsub.add_option(option="-j", value="y")
    aimsub.add_option(option="-o", value="AIMALL.log")
    aimsub.add_option(option="-e", value="AIMALL.err")
    aimsub.add_option(option="-S", value="/bin/bash")

    aimsub.add_path("~/AIMALL")

    # wfns = FileTools.get_files_in(dir, "*.wfn")

    for i in range(len(wfns)):
        wfn = wfns[i]
        job = "%s/JOB%d.log" % (dir.rstrip("/"), i+1)
        aimsub.add_job(wfn, options=job)

    aimsub.write_script()


def formatGJF(fname, coordinates=None):
    global POTENTIAL
    global BASIS_SET

    gjf = GJF(fname, potential=POTENTIAL, basis_set=BASIS_SET)

    if BASIS_SET == "gen":
        gjf.add_keywords(["6D", "10F", "guess=huckel", "integral=(uncontractaobasis)"])
        gjf.gen_basis_set("truncated")

    gjf.add_keywords(["nosymm"])

    if not coordinates:
        coordinates = FileTools.get_coordinates(fname)
    gjf.add_coordinates(coordinates)

    gjf.write_gjf()


def checkWFNs(gjf_dir, wfn_dir):
    global FILE_STRUCTURE

    gjfs_in_gjf_dir = FileTools.get_files_in(gjf_dir, "*.gjf")
    wfns_in_gjf_dir = FileTools.get_files_in(gjf_dir, "*.wfn")
    wfns_in_wfn_dir = FileTools.get_files_in(wfn_dir, "*.wfn")

    all_wfns = wfns_in_gjf_dir + wfns_in_wfn_dir

    if len(all_wfns) != len(gjfs_in_gjf_dir):
        print("WFN(s) missing\n%d GJFs\n%d WFNs\n\n%d WFNs Missing\n\n" % (len(gjfs_in_gjf_dir), len(all_wfns),
                                                                           len(gjfs_in_gjf_dir) - len(all_wfns)))
        gjfs = [(FileTools.get_base(i), i) for i in gjfs_in_gjf_dir]
        wfns = [FileTools.get_base(i) for i in all_wfns]

        missing_gjfs = []
        for gjf in gjfs:
            if gjf[0] not in wfns:
                missing_gjfs.append(gjf[1])

        createGaussScript(gjf_dir, files=missing_gjfs)
        CSFTools.submit_scipt("GaussSub.sh", exit=True)
    else:
        print("\nAll wfns complete\n")


def submitTrainingGJFs():
    global FILE_STRUCTURE
    global BASIS_SET
    global FORMAT_GJFS

    gjf_dir = FILE_STRUCTURE.get_file_path("ts_gjf")
    gjfs = FileTools.get_files_in(gjf_dir, "*.gjf")

    training_set = Points(gjfs=gjfs, training_set=True)

    if FORMAT_GJFS:
        if BASIS_SET == "gen":
            training_set.format_gjfs(keywords=["6D", "10F", "guess=huckel", "integral=(uncontractaobasis)"])
        else:
            training_set.format_gjfs()
        training_set.write_gjfs()

    training_set.create_submission_script(type="gaussian", name="GaussSub.sh", submit=True, exit=False)


def submitWFNs(DirectoryLabel=None, DirectoryPath=None):
    global FILE_STRUCTURE
    global POTENTIAL
    global AIMALL_CORE_COUNT

    if DirectoryLabel:
        dir_location_start = ""

        training_set_labels = ["TRAINING_SET", "TRAINING", "TS"]
        sample_set_labels = ["SAMPLE_POOL", "SAMPLE", "SP", "SAMPLE_SET"]

        if DirectoryLabel.upper() in training_set_labels:
            dir_location_start = "ts"
        elif DirectoryLabel.upper() in sample_set_labels:
            dir_location_start = "sp"
        else:
            print("\nUnknown Directory Label: %s" % DirectoryLabel)
            print("Known Directory Labels:")
            print("  Training Set:")
            print(training_set_labels)
            print("  Sample Pool:")
            print(sample_set_labels)
            print("\nChange Your Directory Label or Create Your Own")
            quit()

        gjf_dir = FILE_STRUCTURE.get_file_path("%s_gjf" % dir_location_start)
        wfn_dir = FILE_STRUCTURE.get_file_path("%s_wfn" % dir_location_start)
        aimall_dir = FILE_STRUCTURE.get_file_path("%s_aimall" % dir_location_start)

    elif DirectoryPath:
        if not DirectoryPath.endswith("/"):
            DirectoryPath += "/"
        gjf_dir = DirectoryPath
        wfn_dir = DirectoryPath + "WFN/"
        aimall_dir = DirectoryPath + "AIMALL/"
    else:
        print("\nPlease Specify A DirectoryLabel or DirectoryPath to WFN files")
        quit()

    FileTools.make_directory(wfn_dir)
    FileTools.make_clean_directory(aimall_dir)

    FileTools.move_files(gjf_dir, wfn_dir, ".wfn")
    if POTENTIAL == "B3LYP":
        FileTools.add_functional(wfn_dir, POTENTIAL)
    FileTools.copy_files(wfn_dir, aimall_dir, ".wfn")
    checkWFNs(gjf_dir, wfn_dir)

    FileTools.remove_files(gjf_dir, ".log")

    aimsub = SubmissionScript("AIMSub.sh", type="aimall", cores=AIMALL_CORE_COUNT)

    aimsub.add_option(option="-j", value="y")
    aimsub.add_option(option="-o", value="AIMALL.log")
    aimsub.add_option(option="-e", value="AIMALL.err")
    aimsub.add_option(option="-S", value="/bin/bash")

    aimsub.add_path("~/AIMALL")

    wfns = FileTools.get_files_in(aimall_dir, "*.wfn")

    for i in range(len(wfns)):
        wfn = wfns[i]
        job = "%s/JOB%d.log" % (aimall_dir, i+1)
        aimsub.add_job(wfn, options=job)

    aimsub.write_script()

    CSFTools.submit_scipt(aimsub.name, exit=True)


def submitTrainingWFNs():
    submitWFNs(DirectoryLabel="training_set")


def makeTrainingSets():
    global FILE_STRUCTURE
    global AUTO_SUBMISSION_MODE
    global FEREBUS_CORE_COUNT

    gjf_dir = FILE_STRUCTURE.get_file_path("ts_gjf")
    aimall_dir = FILE_STRUCTURE.get_file_path("ts_aimall")
    fereb_dir = FILE_STRUCTURE.get_file_path("ts_ferebus")

    FileTools.make_clean_directory(fereb_dir)
    FileTools.cleanup_aimall_dir(aimall_dir, split_into_atoms=False)

    gjfs = FileTools.get_files_in(gjf_dir, "*.gjf")
    int_directories = FileTools.get_files_in(aimall_dir, "*_atomicfiles/")

    training_set = Points(gjfs=gjfs, int_directories=int_directories)
    training_set.make_training_set()

    if not AUTO_SUBMISSION_MODE:
        training_set.create_submission_script(type="ferebus", name="FereSub.sh", submit=True, exit=False, sync=True)
        moveIQAModels()
    else:
        sys.exit(0)


def makeMPoleTrainingSets():
    global FILE_STRUCTURE
    global AUTO_SUBMISSION_MODE
    global FEREBUS_CORE_COUNT

    gjf_dir = FILE_STRUCTURE.get_file_path("ts_gjf")
    aimall_dir = FILE_STRUCTURE.get_file_path("ts_aimall")
    fereb_dir = FILE_STRUCTURE.get_file_path("ts_ferebus")

    FileTools.make_clean_directory(fereb_dir)
    FileTools.cleanup_aimall_dir(aimall_dir, split_into_atoms=False)

    gjfs = FileTools.get_files_in(gjf_dir, "*.gjf")
    int_directories = FileTools.get_files_in(aimall_dir, "*_atomicfiles/")

    training_set = Points(gjfs=gjfs, int_directories=int_directories)

    training_set.make_training_set(IQA=False)

    if not AUTO_SUBMISSION_MODE:
        training_set.create_submission_script(type="ferebus", name="FereSub.sh", submit=True, exit=False, sync=True)
        moveMPoleModels()
    else:
        sys.exit(0)


def moveIQAModels():
    global SYSTEM_NAME
    global FILE_STRUCTURE

    ferebus_dir = FILE_STRUCTURE.get_file_path("ts_ferebus")
    atom_directories = FileTools.get_atom_directories(ferebus_dir)

    q00_files = []
    for atom_directory in atom_directories:
        if not atom_directory.endswith("/"):
            atom_directory += "/"
        q00_locs = FileTools.get_files_in(atom_directory, "*q00*.txt")
        if len(q00_locs) == 1:
            q00_files.append(q00_locs[0])

    if len(q00_files) == len(atom_directories):
        models_dir = FILE_STRUCTURE.get_file_path("ts_models")
        FileTools.make_clean_directory(models_dir)
        for q00_file in q00_files:
            q00_name = q00_file.split("/")[-1]
            q00_num = q00_name.replace(".txt", "").split("_")[-1]
            model_filename = "%s%s_kriging_IQA_%s.txt" % (models_dir, SYSTEM_NAME, q00_num)
            FileTools.copy_file(q00_file, model_filename)
            FileTools.remove_no_noise(model_filename)
    else:
        print("Error: IQA Models not complete.")
        exit(1)


def moveMPoleModels():
    global SYSTEM_NAME
    global FILE_STRUCTURE

    ferebus_dir = FILE_STRUCTURE.get_file_path("ts_ferebus")
    atom_directories = FileTools.get_atom_directories(ferebus_dir)

    mpole_files = []
    for atom_directory in atom_directories:
        if not atom_directory.endswith("/"):
            atom_directory += "/"
        mpole_locs = FileTools.get_files_in(atom_directory, "*kriging*q*.txt")
        if len(mpole_locs) == 25:
            mpole_files.append(mpole_locs)

    if len(mpole_files) == len(atom_directories):
        models_dir = FILE_STRUCTURE.get_file_path("ts_models")
        FileTools.make_directory(models_dir)
        for mpole_locs in mpole_files:
            for mpole_file in mpole_locs:
                model_filename = models_dir + mpole_file.split("/")[-1]
                FileTools.copy_file(mpole_file, model_filename)
                FileTools.remove_no_noise(model_filename)
    else:
        print("Error: MPole Models not complete.")
        exit(1)


def moveModelsToLog():
    global SYSTEM_NAME
    global FILE_STRUCTURE
    global TRAINING_POINTS_TO_USE
    
    model_dir = FILE_STRUCTURE.get_file_path("ts_models")
    log_dir = FILE_STRUCTURE.get_file_path("log")

    log_loc = log_dir + SYSTEM_NAME + str(TRAINING_POINTS_TO_USE).zfill(4) + "/"

    FileTools.make_clean_directory(log_loc)
    FileTools.move_files(model_dir, log_loc, ".txt")


def submitSampleGJFs():
    global FILE_STRUCTURE
    global BASIS_SET
    global FORMAT_GJFS

    gjf_dir = FILE_STRUCTURE.get_file_path("sp_gjf")
    gjfs = FileTools.get_files_in(gjf_dir, "*.gjf")

    sample_pool = Points(gjfs=gjfs)

    if FORMAT_GJFS:
        if BASIS_SET == "gen":
            sample_pool.format_gjfs(keywords=["6D", "10F", "guess=huckel", "integral=(uncontractaobasis)"])
        else:
            sample_pool.format_gjfs()
        sample_pool.write_gjfs()

    sample_pool.create_submission_script(type="gaussian", name="GaussSub.sh", submit=True, exit=False)


def submitSampleWFNs():
    submitWFNs(DirectoryLabel="sample_set")


def getSampleAIMALLEnergies():
    global FILE_STRUCTURE
    global IMPORTANT_FILES

    gjf_dir = FILE_STRUCTURE.get_file_path("sp_gjf")
    aimall_dir = FILE_STRUCTURE.get_file_path("sp_aimall")

    FileTools.cleanup_aimall_dir(aimall_dir, split_into_atoms=False)


def normalize(l):
    min_val = min(l)
    max_val = max(l)
    min_max = max_val - min_val 
    return [(x - min_val)/min_max for x in l]


def calculatePredictions(calculate_variance=True, return_models=False, calculate_cv_errors=False,
                         return_geometries=False):
    global ALF
    global FILE_STRUCTURE

    gjf_dir = FILE_STRUCTURE.get_file_path("sp_gjf")
    gjfs = FileTools.get_files_in(gjf_dir, "*.gjf")

    sample_geometries = []
    sample_features = []
    for gjf in gjfs:
        coord_lines = FileTools.get_coordinates(gjf)
        atoms = []
        coordinates = []
        for coord_line in coord_lines:
            line_split = coord_line.split()
            atoms.append(coord_line[0])
            coordinates.append([float(line_split[1]), float(line_split[2]), float(line_split[3])])
        if calculate_cv_errors:
            sample_geometries.append(GeometryData(gjf, atoms, coordinates))
        sample_features.append(calcFeats(ALF, coordinates))

    x_values = []
    for i in range(len(sample_features[0])):
        x = [j[i] for j in sample_features]
        x_values.append(x)


    model_dir = FILE_STRUCTURE.get_file_path("ts_models")
    iqa_models = FileTools.get_files_in(model_dir, "*IQA*.txt")

    predictions, s_values, cv_errors, models = [], [], [], []

    for atom in range(len(iqa_models)):
        iqa_model = MODEL(iqa_models[atom])

        cv_errors.append(iqa_model.calcCVError())

        predictions.append(iqa_model.predict(x_values[atom]))
        if calculate_variance:
            s_values.append(iqa_model.variance(x_values[atom]))
        if return_models:
            models.append(iqa_model)

    total_predictions, total_s_values = [], []

    for i in range(len(predictions[0])):
        pred_sum, s_sum = 0.0, 0.0
        for j in range(len(predictions)):
            pred_sum += predictions[j][i]
            if calculate_variance:
                s_sum += s_values[j][i]
        total_predictions.append(pred_sum)
        if calculate_variance:
            total_s_values.append(s_sum)

    sample_cv_errors = []

    if calculate_cv_errors:
        thetas = []

        for model in models:
            thetas.append(model.theta_values)

        total_cv_errors = []
        for i in range(len(cv_errors[0])):
            cv_sum = 0.0
            for j in range(len(cv_errors)):
                cv_sum += cv_errors[j][i]
            total_cv_errors.append(cv_sum)

        ts_gjf_dir = FILE_STRUCTURE.get_file_path("ts_gjf")
        ts_gjfs = FileTools.get_files_in(ts_gjf_dir, "*.gjf")

        training_geometries = []

        for gjf, cv_error in zip(ts_gjfs, total_cv_errors):
            coord_lines = FileTools.get_coordinates(gjf)
            atoms = []
            coordinates = []
            for coord_line in coord_lines:
                line_split = coord_line.split()
                atoms.append(coord_line[0])
                coordinates.append([float(line_split[1]), float(line_split[2]), float(line_split[3])])
            geometry = GeometryData(gjf, atoms, coordinates)
            geometry.set_cv_error(cv_error)
            training_geometries.append(geometry)

        for sample_geometry in sample_geometries:
            for i in range(len(training_geometries)):
                sample_geometry.get_distance_to(training_geometries[i], atom=i, theta=thetas)

        for sample_geometry in sample_geometries:
            sample_cv_errors.append(sample_geometry.cv_error)


    values_to_return = {"predictions" : total_predictions}

    if calculate_variance:
        values_to_return["variance"] = total_s_values

    if return_models:
        values_to_return["models"] = models

    if calculate_cv_errors:
        values_to_return["cv_errors"] = sample_cv_errors

    if return_geometries:
        values_to_return["sample_geometries"] = sample_geometries

    return values_to_return


def calcEPE(Ecv, s, alpha):
    return alpha * Ecv + (1 - alpha) * s


def calculateErrors():
    global SYSTEM_NAME
    global POINTS_PER_ITERATION
    global MULTIPLE_ADDITION_MODE
    global PRECALCULATE_AIMALL
    global TRAINING_POINTS_TO_USE

    values_dictionary = calculatePredictions(calculate_variance=True, return_models=True, calculate_cv_errors=True,
                                             return_geometries=True)

    predictions = values_dictionary["predictions"]
    variance = values_dictionary["variance"]
    models: List[MODEL] = values_dictionary["models"]
    cv_errors = values_dictionary["cv_errors"]
    sample_geometries = values_dictionary["sample_geometries"]

    first_iteration = True
    for model in models:
        if model.nTrain > 2*model.nFeats:
            first_iteration = False
            break

    alpha = 0.5
    if not first_iteration:
        with open("ErrorFile.csv", "r") as f:
            data = f.readlines()

        data = data[-min(len(data)-1, POINTS_PER_ITERATION):]

        nalpha = 0.0
        for data_line in data:
            line_split = data_line.split(",")
            pEtrue = float(line_split[1])
            pEcv = float(line_split[2])

            nalpha += 0.99 * min(0.5*(pEtrue/pEcv), 1.0)

        alpha = nalpha/len(data)
    else:
        with open("ErrorFile.csv", "w+") as f:
            f.write("No.,Etrue,Ecv,s2,alpha\n")

    EPE = []

    if NORMALIZE:
        n_cv_errors = normalize(cv_errors)
        n_variance = normalize(variance)
    else:
        n_cv_errors = cv_errors
        n_variance = variance

    for i in range(len(n_cv_errors)):
        EPE.append((i, calcEPE(n_cv_errors[i], n_variance[i], alpha)))

    MEPE = []
    EPE = UsefulTools.sorted_tuple(EPE, 1, reverse=True)
    if MULTIPLE_ADDITION_MODE == "manifold":
        sampled_training_points = []
        for i in range(len(EPE)):
            if sample_geometries[EPE[i][0]].cv_atom not in sampled_training_points:
                MEPE.append(EPE[i])
                sampled_training_points.append(sample_geometries[EPE[i][0]].cv_atom)
    elif MULTIPLE_ADDITION_MODE == "multiple":
        MEPE = list(EPE)

    MEPE = MEPE[:min(len(EPE), POINTS_PER_ITERATION)]
    MEPE = sorted(MEPE, reverse=True)

    if PRECALCULATE_AIMALL:
        training_gjf_dir = FILE_STRUCTURE.get_file_path("ts_gjf")
        training_wfn_dir = FILE_STRUCTURE.get_file_path("ts_wfn")
        training_int_dir = FILE_STRUCTURE.get_file_path("ts_aimall")
        training_set_size = len(FileTools.get_files_in(training_gjf_dir, "*.gjf", sorting="none"))
    else:
        training_gjf_dir = FILE_STRUCTURE.get_file_path("temp")
        FileTools.make_clean_directory(training_gjf_dir)
        training_set_size = 0

    log_dir = FILE_STRUCTURE.get_file_path("log")
    if first_iteration:
        FileTools.make_clean_directory(log_dir)
    model_dir = "%s%s%s" % (log_dir, SYSTEM_NAME, str(TRAINING_POINTS_TO_USE).zfill(4))
    os.mkdir(model_dir)
    FileTools.copy_files(FILE_STRUCTURE.get_file_path("ts_models"), model_dir, ".txt")

    sample_gjf_dir = FILE_STRUCTURE.get_file_path("sp_gjf")
    sample_gjfs = FileTools.get_files_in(sample_gjf_dir, "*.gjf", sorting="natural")

    if PRECALCULATE_AIMALL:
        sample_wfn_dir = FILE_STRUCTURE.get_file_path("sp_wfn")
        sample_wfns = FileTools.get_files_in(sample_wfn_dir, "*.wfn", sorting="natural")

        sample_int_dir = FILE_STRUCTURE.get_file_path("sp_aimall")
        sample_ints = FileTools.get_files_in(sample_int_dir, "*_atomicfiles/", sorting="natural")

        sample_aimall_dir = FILE_STRUCTURE.get_file_path("sp_aimall")
        sample_atom_directories = FileTools.get_directories(sample_aimall_dir)

    for i in range(len(MEPE)):
        index = MEPE[i][0]
        print(index+1)

        new_base = SYSTEM_NAME + str(training_set_size + i + 1).zfill(4)

        sample_gjf = sample_gjfs[index]
        training_gjf = "%s%s.gjf" % (training_gjf_dir, new_base)
        FileTools.move_file(sample_gjf, training_gjf)
        print("Moved %s to %s" % (sample_gjf, training_gjf))

        if PRECALCULATE_AIMALL:
            sample_wfn = sample_wfns[index]
            training_wfn = "%s%s.wfn" % (training_wfn_dir, new_base)
            FileTools.move_file(sample_wfn, training_wfn)
            print("Moved %s to %s" % (sample_wfn, training_wfn))

            sample_int = sample_ints[index]
            training_int_atomicfiles = "%s%s_atomicfiles/" % (training_int_dir, new_base)
            FileTools.move_file(sample_int, training_int_atomicfiles)
            print("Moved %s to %s" % (sample_int, training_int_atomicfiles))

            training_int_files = FileTools.get_files_in(training_int_atomicfiles, "*.int")
            e_iqa = 0.0
            for training_int_file in training_int_files:
                int_data = INT(training_int_file)
                e_iqa += int_data.IQA_terms["E_IQA(A)"]

                int_base = FileTools.get_base(training_int_file)
                os.rename(training_int_file, training_int_file.replace(int_base, new_base))

            Etrue = (e_iqa - predictions[index])**2

            with open("ErrorFile.csv", "a") as f:
                f.write("%s,%.16f,%.16f,%.16f,%.16f\n" % (str(index+1).zfill(4), Etrue, cv_errors[index], variance[index],
                                                        alpha))
        else:
            with open("ErrorFile.csv", "a") as f:
                f.write("%s,%s,%.16f,%.16f,%.16f\n" % (str(index+1).zfill(4), predictions[index], cv_errors[index], variance[index],
                                                        alpha))

    if not PRECALCULATE_AIMALL:
        updateTempGJFs()
        if not AUTO_SUBMISSION_MODE:
            with open("jid.txt", "w") as jid:
                pJID = submit_gjfs(None)
                jid.write("{}\n".format(pJID))
                pJID = submit_wfns(pJID)
                jid.write("{}\n".format(pJID))
                pJID = submit_python(pJID, 1, 2)
                jid.write("{}\n".format(pJID))
        sys.exit(0)

    print("")


def updateTempGJFs():
    global FILE_STRUCTURE

    temp_dir = FILE_STRUCTURE.get_file_path("temp")
    gjfs = FileTools.get_files_in(temp_dir, "*.gjf")

    temp_set = Points(gjfs=gjfs)
    temp_set.format_gjfs()
    temp_set.write_gjfs()


def edit_DLPOLY():
    global DLPOLY_NUMBER_OF_STEPS
    global DLPOLY_TIMESTEP
    global DLPOLY_TEMPERATURE
    global DLPOLY_PRINT_EVERY

    global CONFIG

    default_DLPOLY_NUMBER_OF_STEPS = DLPOLY_NUMBER_OF_STEPS
    default_DLPOLY_TIMESTEP = DLPOLY_TIMESTEP
    default_DLPOLY_TEMPERATURE = DLPOLY_TEMPERATURE
    default_DLPOLY_PRINT_EVERY = DLPOLY_PRINT_EVERY

    while True:
        print("")
        print("###################")
        print("# DLPOLY Settings #")
        print("###################")
        print("")
        print("[1] Number Of Steps")
        print("[2] Timestep")
        print("[3] Temperature")
        print("[4] Print Stats Every")
        print("")
        print("[p] Show Current Values")
        print("")
        print("[b] Go back")
        print("[0] Exit")
        ans = input()
        if "b" in ans.lower():
            break
        elif ans == "0":
            sys.exit()
        elif ans == "1":
            DLPOLY_NUMBER_OF_STEPS = int(input("Input Number Of Steps:"))
            if DLPOLY_NUMBER_OF_STEPS != default_DLPOLY_NUMBER_OF_STEPS:
                CONFIG.add_key_val("DLPOLY_NUMBER_OF_STEPS", DLPOLY_NUMBER_OF_STEPS)
                CONFIG.write_key_vals()
        elif ans == "2":
            DLPOLY_TIMESTEP = float(input("Input Timestep:"))
            if DLPOLY_TIMESTEP != default_DLPOLY_TIMESTEP:
                CONFIG.add_key_val("DLPOLY_TIMESTEP", DLPOLY_TIMESTEP)
                CONFIG.write_key_vals()
        elif ans == "3":
            DLPOLY_TEMPERATURE = int(input("Input Temperature:"))
            if DLPOLY_TEMPERATURE != default_TEMPERATURE:
                CONFIG.add_key_val("DLPOLY_TEMPERATURE", DLPOLY_TEMPERATURE)
                CONFIG.write_key_vals()
        elif ans == "4":
            DLPOLY_PRINT_EVERY = int(input("Input Print Frequency:"))
            if DLPOLY_PRINT_EVERY != default_DLPOLY_PRINT_EVERY:
                CONFIG.add_key_val("DLPOLY_PRINT_EVERY", DLPOLY_PRINT_EVERY)
                CONFIG.write_key_vals()
        elif ans == "p":
            print("")
            print("%s = %d" % ("DLPOLY_NUMBER_OF_STEPS", DLPOLY_NUMBER_OF_STEPS))
            print("%s = %f" % ("DLPOLY_TIMESTEP       ", DLPOLY_TIMESTEP))
            print("%s = %f" % ("DLPOLY_TEMPERATURE    ", DLPOLY_TEMPERATURE))
            print("%s = %d" % ("DLPOLY_PRINT_EVERY    ", DLPOLY_PRINT_EVERY))
            print("")
        else:
            if ans in options:
                options[ans]()
            else:
                print("%s is not a valid option" % ans)


def run_DLPOLY_on_LOG():
    global FILE_STRUCTURE
    global DLPOLY_CORE_COUNT

    dlpoly_base_dir = FILE_STRUCTURE.get_file_path("dlpoly")
    FileTools.make_clean_directory(dlpoly_base_dir)

    log_dir = FILE_STRUCTURE.get_file_path("log")
    model_dirs = FileTools.get_files_in(log_dir, "*/")

    sample_gjf_dir = FILE_STRUCTURE.get_file_path("sp_gjf")
    sample_gjfs = FileTools.get_files_in(sample_gjf_dir, "*.gjf")
    gjf_file = sample_gjfs[0]

    atoms = UsefulTools.get_atoms()

    dlpolysub = SubmissionScript("DLPOLYsub.sh", type="dlpoly", cores=DLPOLY_CORE_COUNT)

    if MACHINE == "csf2":
        dlpolysub.add_module("compilers/gcc/6.3.0")
    elif MACHINE == "csf3":
        dlpolysub.add_module("compilers/gcc/8.2.0")

    dlpoly_working_directories = []

    for model_directory in model_dirs:
        dlpoly_working_dir = model_directory.replace(log_dir, dlpoly_base_dir)
        dlpoly_working_model_dir = dlpoly_working_dir + "model_krig"
        os.mkdir(dlpoly_working_dir)
        os.mkdir(dlpoly_working_model_dir)
        dlpoly_working_directories.append(dlpoly_working_dir)
        FileTools.copy_files(model_directory, dlpoly_working_model_dir, ".txt")

        model_file = FileTools.get_files_in(dlpoly_working_model_dir, "*.txt")[0]
        number_of_training_points = MODEL(model_file).nTrain

        dlpoly = DLPOLYsetup(dlpoly_working_dir, atoms, number_of_training_points)

        dlpoly.write_gjf_to_config(gjf_file)

        dlpolysub.add_job(dlpoly_working_dir)

    dlpolysub.write_script()

    ans = ""
    while True:
        ans = input("Would you like to wait for DLPOLY to complete? [Y/N]")
        ans = ans.upper()

        if ans in  ["Y", "N", "YES", "NO"]:
            break
        else:
            print("%s not a valid answer\n" % ans)

    if ans in ["Y", "YES"]:
        CSFTools.submit_scipt(dlpolysub.name, sync=True)
    else:
        CSFTools.submit_scipt(dlpolysub.name, exit=True)


def submit_DLPOLY_to_gaussian():
    global FILE_STRUCTURE

    # Setup file locations
    dlpoly_base_dir = FILE_STRUCTURE.get_file_path("dlpoly")
    dlpoly_gjf_dir = dlpoly_base_dir + "GJF/"
    FileTools.make_directory(dlpoly_gjf_dir)

    trajectory_files = FileTools.get_files_in(dlpoly_base_dir, "*/TRAJECTORY.xyz")

    for trajectory_file in trajectory_files:
        coordinates = FileTools.get_last_coordinates(trajectory_file)
        model_name = trajectory_file.split("/")[-2]

        # e.g DLPOLY/WATER0006/TRAJECTORY.xyz >> DLPOLY/GJF/WATER0006.gjf
        gjf_fname = dlpoly_gjf_dir + model_name + ".gjf"
        gjf = formatGJF(gjf_fname, coordinates=coordinates)

    createGaussScript(dlpoly_gjf_dir, name="DLPOLYGaussSub.sh")

    ans = ""
    while True:
        ans = input("Would you like to wait for DLPOLY to complete? [Y/N]")
        ans = ans.upper()
        if ans in  ["Y", "N", "YES", "NO"]:
            break
        else:
            print("%s not a valid answer\n" % ans)

    if ans in ["Y", "YES"]:
        CSFTools.submit_scipt("DLPOLYGaussSub.sh", sync=True)
        get_DLPOLY_WFN_energies()
    else:
        CSFTools.submit_scipt("DLPOLYGaussSub.sh", exit=True)


def get_DLPOLY_WFN_energies():
    global FILE_STRUCTURE

    # Setup file locations
    dlpoly_base_dir = FILE_STRUCTURE.get_file_path("dlpoly")
    wfns = FileTools.get_files_in(dlpoly_base_dir, "*/*.wfn", sorting="natural")

    print("\n%d wfns found.\n" % len(wfns))
    if len(wfns) > 0:
        with open(dlpoly_base_dir + "Energies.txt", "w+") as o:
            for wfn in wfns:
                with open(wfn, "r") as f:
                    last_line = f.readlines()[-1]
                wfn_energy = re.findall("[+-]?\d+.\d+", last_line)[0]
                print("%d %s" % (int(re.findall("\d+", FileTools.get_base(wfn))[0]), wfn_energy))
                o.write("%s\t%s\n" % (FileTools.get_base(wfn), wfn_energy))
        print("\nWrote All Energies to %s\n" % dlpoly_base_dir + "Energies.txt", "w+")


def submit_python(pJID, iter, mode):
    pysub = SubmissionScript("pysub.sge", type="python")
    pysub.add_option(option="-N", value=sys.argv[0])
    pysub.add_option(option="-S", value="/bin/bash")
    pysub.add_option(option="-o", value="outputfile.log")
    pysub.add_option(option="-j", value="y")
    pysub.add_job(sys.argv[0], "-a -i %d -s %d" % (iter, mode))
    pysub.write_script()

    if pJID:
        pJID = CSFTools.submit_scipt(pysub.name, hold_jid=pJID, return_jid=True)
    else:
        pJID = CSFTools.submit_scipt(pysub.name, return_jid=True)

    print("Submitted %s\t\tjid:%s" % (pysub.name, pJID))
    return pJID


def submit_ferebus(pJID, gjf_example):
    fereb_dir = FILE_STRUCTURE.get_file_path("ts_ferebus")
    training_set = Points()
    coords = FileTools.get_coordinates(gjf_example)
    atom_directories = []
    for i, line in enumerate(coords):
        atom = line.split()[0]
        atom_directories.append("%s%s%d/" % (fereb_dir, atom, i+1))
    training_set.training_set_directories = atom_directories
    training_set.create_submission_script(type="ferebus", name="FereSub.sh", submit=False)

    pJID = CSFTools.submit_scipt(training_set.submission_script.name, hold_jid=pJID, return_jid=True)
    print("Submitted %s\t\tjid:%s" % (training_set.submission_script.name, pJID))
    return pJID


def checkFunctional():
    global FILE_STRUCTURE
    global POTENTIAL
    if POTENTIAL == "B3LYP":
        wfn_dir = FILE_STRUCTURE.get_file_path("temp")
        FileTools.add_functional(wfn_dir, POTENTIAL)


def moveTemp2Train():
    global FILE_STRUCTURE
    global POINTS_PER_ITERATION

    ts_size = get_ts_size()

    temp_dir = FILE_STRUCTURE.get_file_path("temp")

    gjfs = FileTools.get_files_in(temp_dir, "*.gjf")
    wfns = FileTools.get_files_in(temp_dir, "*.wfn")

    gjfs = FileTools.increment_files(gjfs, ts_size)
    wfns = FileTools.increment_files(wfns, ts_size)

    FileTools.cleanup_aimall_dir(temp_dir, remove_wfns=False)
    int_directories = FileTools.get_files_in(temp_dir, "*_atomicfiles/")
    int_directories = FileTools.increment_files(int_directories, ts_size)

    for int_directory in int_directories:
        int_files = FileTools.get_files_in(int_directory, "*.int")
        FileTools.increment_files(int_files, ts_size)
    
    true_values = []
    points_to_move = Points(int_directories=int_directories)
    for point in points_to_move:
        e_iqa = 0.0
        for atom, int_data in point.int.items():
            e_iqa += int_data.IQA_terms["E_IQA(A)"]
        true_values.append(e_iqa)
    
    with open("ErrorFile.csv", "r") as f:
        data = f.readlines()

    i = max(len(data) - POINTS_PER_ITERATION, 1)
    j = 0
    while i < len(data):
        line = data[i]
        line = line.split(",")
        line[1] = str((true_values[j] - float(line[1]))**2)
        data[i] = ",".join(line) + "\n"
        i += 1
        j += 1

    with open("ErrorFile.csv", "w") as f:
        for line in data:
            f.write(line.rstrip() + "\n")
    
    gjf_dir = FILE_STRUCTURE.get_file_path("ts_gjf")
    wfn_dir = FILE_STRUCTURE.get_file_path("ts_wfn")
    aim_dir = FILE_STRUCTURE.get_file_path("ts_aimall")

    FileTools.move_files(temp_dir, gjf_dir, ".gjf")
    FileTools.move_files(temp_dir, wfn_dir, ".wfn")
    FileTools.move_directories(temp_dir, aim_dir, "_atomicfiles")

    FileTools.remove_directory(temp_dir)


def submit_gjfs(pJID):
    global POINTS_PER_ITERATION
    global SYSTEM_NAME
    global FILE_STRUCTURE

    temp_dir = FILE_STRUCTURE.get_file_path("temp")
    gjf_files = []

    for i in range(POINTS_PER_ITERATION):
        gjf_file = temp_dir + SYSTEM_NAME + str(i+1).zfill(4) + ".gjf"
        gjf_files.append(gjf_file)

    createGaussScript(temp_dir, files=gjf_files)
    pJID = CSFTools.submit_scipt("GaussSub.sh", return_jid=True, hold_jid=pJID)
    print("Submitted %s\t\tjid:%s" % ("GaussSub.sh", pJID))
    return pJID


def submit_wfns(pJID):
    global POINTS_PER_ITERATION
    global SYSTEM_NAME
    global FILE_STRUCTURE

    temp_dir = FILE_STRUCTURE.get_file_path("temp")
    wfn_files = []

    for i in range(POINTS_PER_ITERATION):
        wfn_file = temp_dir + SYSTEM_NAME + str(i+1).zfill(4) + ".wfn"
        wfn_files.append(wfn_file)
    
    createAimScript(temp_dir, files=wfn_files)
    pJID = CSFTools.submit_scipt("AIMSub.sh", return_jid=True, hold_jid=pJID)
    print("Submitted %s\t\tjid:%s" % ("AIMSub.sh", pJID))
    return pJID


def autoRun(submit=True):
    global MAX_ITERATION
    global STEP
    global AUTO_SUBMISSION_MODE
    global FILE_STRUCTURE

    AUTO_SUBMISSION_MODE = True
    gjf_example = FileTools.get_files_in(FILE_STRUCTURE.get_file_path("ts_gjf"), "*.gjf")[0]

    pJID = None
    if submit:
        with open("jid.txt", "w+") as jid:
            for i in range(MAX_ITERATION):
                pJID = submit_python(pJID, i, 0)
                jid.write("%s\n" % pJID)
                
                pJID = submit_ferebus(pJID, gjf_example)
                jid.write("%s\n" % pJID)
                
                pJID = submit_python(pJID, i, 1)
                jid.write("%s\n" % pJID)

                if not PRECALCULATE_AIMALL:
                    pJID = submit_gjfs(pJID)
                    jid.write("%s\n" % pJID)
                    pJID = submit_python(pJID, i, 2)
                    jid.write("%s\n" % pJID)
                    pJID = submit_wfns(pJID)
                    jid.write("%s\n" % pJID)
                    pJID = submit_python(pJID, i, 3)
                    jid.write("%s\n" % pJID)
    else:
        if STEP == 0:
            makeTrainingSets()
        elif STEP == 1:
            moveIQAModels()
            calculateErrors()
        elif STEP == 2:
            checkFunctional()
        elif STEP == 3:
            moveTemp2Train()


    sys.exit(0)


def makeFormattedFiles():
    global FILE_STRUCTURE
    global AUTO_SUBMISSION_MODE
    global FEREBUS_CORE_COUNT

    gjf_dir = FILE_STRUCTURE.get_file_path("ts_gjf")
    aimall_dir = FILE_STRUCTURE.get_file_path("ts_aimall")

    atom_directories = FileTools.natural_sort(FileTools.get_atom_directories(aimall_dir))

    gjf_data = []
    gjf_files = FileTools.get_files_in(gjf_dir, "*.gjf")
    for gjf in gjf_files:
        gjf_name = gjf.split("/")[-1].replace(".gjf", "")
        gjf_coordinates, atoms = [], []

        atom_counter = 1
        coordinates = FileTools.get_coordinates(gjf)
        for coordinate in coordinates:
            coordinate_split = coordinate.split()
            atom = coordinate_split[0] + str(atom_counter)
            atom_coordinates = []
            for i in range(1,4):
                atom_coordinates.append(float(coordinate_split[i]))
            atoms.append(atom)
            gjf_coordinates.append(atom_coordinates)
            atom_counter += 1

        gjf_data.append(GeometryData(gjf_name, atoms, gjf_coordinates))

    for directory in atom_directories:
        # Setup Ferebus Atom Directories
        atom = str(directory.split("/")[-1])

        # Read Data From Int Files
        int_files = FileTools.get_files_in(directory, "*.int")
        ints = []
        for int_file in int_files:
            ints.append(INT(int_file))

        if not os.path.isdir("Test/"):
            os.mkdir("Test/")

        training_set_file = "Test/" + atom + "_TRAINING_SET.csv"

        with open(training_set_file, "w+") as f:
            row_count = 1
            for gjf_i, int_i in zip(gjf_data, ints):
                features = gjf_i.get_atom_features(atom)
                formated_features = ["{0:11.8f}".format(i) for i in features]

                features_string = ",".join(formated_features)

                mpoles = []

                eiqa = str(int_i.IQA_terms["E_IQA(A)"])

                multipole_moments = int_i.multipole_moments
                mpole_key_vals = multipole_moments.items()

                number_of_mpoles = 25

                mpole_names = [x[0] for x in mpole_key_vals][:number_of_mpoles]
                mpoles = [str(x[1]) for x in mpole_key_vals][:number_of_mpoles]

                mpole_string = ",".join(mpoles)
                row_number = str(row_count).zfill(4)

                if row_count == 1:
                    feature_names = []
                    for i in range(len(formated_features)):
                        feature_names.append("f%d" % (i+1))
                    f.write("No.,%s,%s,IQA\n" % (",".join(feature_names), ",".join(mpole_names)))
                f.write("%s,%s,%s,%s\n" % (row_number, features_string, mpole_string, eiqa))
                row_count += 1


def statistics_summary(l, name=None):
    title_character = "="
    summary_title = "Statistics Summary"
    if l:
        max_len = max(len(name), len(summary_title)) + 2
    else:
        max_len = len(summary_title) + 2
    print("")
    print(title_character * max_len)
    print(summary_title.center(max_len, " "))
    if name:
        print(("%s" % name).center(max_len, " "))
    print(title_character * max_len)
    print("")
    print("Total Values: %d" % len(l))
    print("")
    print("Max Value:    %f" % max(l))
    print("Min Value:    %f" % min(l))
    print("Mean:         %f" % np.mean(l))
    print("Variance:     %f" % np.std(l))
    print("")


def calculate_S_Curves(model_files):
    models = []
    print("\nReading Models")
    for model_file in tqdm(model_files):
        models.append(MODEL(model_file))
    
    gjf_dir = FILE_STRUCTURE.get_file_path("sp_gjf")
    gjfs = FileTools.get_files_in(gjf_dir, "*.gjf")

    aim_dir = FILE_STRUCTURE.get_file_path("sp_aimall")
    int_dirs = FileTools.get_files_in(aim_dir, "*_atomicfiles/")

    print("\nReading Test Data")
    test_set = Points(gjfs=gjfs, int_directories=int_dirs)

    print("\nMaking Predictions...")
    predictions = test_set.predict(models)

    true_values = []
    types = []

    print("\nSorting True Values...")
    t = tqdm(models)
    for model in t:
        t.set_description(model.type)
        if model.type not in types:
            int_data = test_set.get_int_data(model.type)
            types.append(model.type)
            for data in int_data:
                true_values.append(data)
    with open("s_curve.csv", "w+") as f:
        line = ""
        for model in models:
            line += "%s_%s_true,%s_%s_pred,%s_%s_diff," % ((model.type, model.number)*3)
        f.write(line.rstrip(",") + "\n")

        for i in range(len(true_values[0])):
            line = ""
            for j in range(len(true_values)):
                true_value = true_values[j][i]
                prediction = predictions[j][i]
                line += "%.16f,%.16f,%.16f," % (true_value, prediction, abs(true_value-prediction))
            f.write(line.rstrip(",") + "\n")


def IQA_S_Curves(model_location):
    model_files = FileTools.get_files_in(model_location, "*IQA*.txt")

    if len(model_files) == 0:
        print("Cannot Find IQA Model Files in %s" % model_location)
        return
    
    calculate_S_Curves(model_files)


def MPole_S_Curves(model_location):
    model_files = FileTools.get_files_in(model_location, "*kriging*q*.txt")

    if len(model_files) == 0:
        print("Cannot Find IQA Model Files in %s" % model_location)
        return
    
    calculate_S_Curves(model_files)


def Both_S_Curves(model_location):
    model_files = FileTools.get_files_in(model_location, "*kriging*.txt")

    if len(model_files) == 0:
        print("Cannot Find IQA Model Files in %s" % model_location)
        return
    
    calculate_S_Curves(model_files)


def s_curves():
    global FILE_STRUCTURE

    current_model = FILE_STRUCTURE.get_file_path("ts_models")

    while True:
        print("")
        print("################")
        print("# S-Curve Menu #")
        print("################")
        print("")
        print("[1] IQA S-Curves")
        print("[2] MPole S-Curves")
        print("[3] Both")
        print("")
        print("[model] Select Model")
        print("Current Model: %s" % current_model)
        print("")
        print("[b] Back to Main")
        print("[0] Exit")

        ans = input("Enter Action:")

        if ans == "b":
            break
        elif ans == "0":
            sys.exit(0)
        elif ans == "1":
            IQA_S_Curves(current_model)
        elif ans == "2":
            MPole_S_Curves(current_model)
        elif ans == "3":
            Both_S_Curves(current_model)


def recovery_errors(wfn_dir="", aimall_dir=""):
    wfns = FileTools.get_files_in(wfn_dir, "*.wfn")
    atomicfiles = FileTools.get_files_in(aimall_dir, "*_atomicfiles/")

    test_set = Points(wfns=wfns, int_directories=atomicfiles)

    wfn_energies = test_set.get_wfn_energies()
    aimall_energies = test_set.get_aimall_energeis()
    atoms = test_set.get_atoms()

    errors = []

    with open("recovery_errors.csv", "w+") as f:
        f.write("No.,%s,AIMAll Energy,WFN Energy,Recovery Error / Ha,Recovery Error / kJ mol^-1\n" % ",".join(atoms))
        for point, atom_energies, wfn_energy in zip(test_set, aimall_energies, wfn_energies):
            mol_energy = sum(atom_energies)
            error_ha = abs(mol_energy-wfn_energy)
            error_kj = error_ha * 2625.5
            atom_energies = [""] * len(atoms)
            for atom, aimall_data in point.int.items():
                atom_energies[atoms.index(atom)] = "%.12f" % aimall_data.IQA_terms["E_IQA(A)"]
            f.write("%s,%s,%.12f,%.12f,%.12f,%.12f\n" % (point.name, ",".join(atom_energies), mol_energy, wfn_energy,
                                                        error_ha, error_kj))
            errors.append(error_kj)
    
    statistics_summary(errors, name="Recovery Error / kJ mol^-1")


def training_recovery_errors():
    global FILE_STRUCTURE
    
    wfn_dir = FILE_STRUCTURE.get_file_path("ts_wfn")
    aimall_dir = FILE_STRUCTURE.get_file_path("ts_aimall")

    recovery_errors(wfn_dir=wfn_dir, aimall_dir=aimall_dir)

def sample_recovery_errors():
    global FILE_STRUCTURE

    wfn_dir = FILE_STRUCTURE.get_file_path("sp_wfn")
    aimall_dir = FILE_STRUCTURE.get_file_path("sp_aimall")

    recovery_errors(wfn_dir=wfn_dir, aimall_dir=aimall_dir)


def recovery_error_menu():
    while True:
        print("")
        print("#######################")
        print("# Recovery Error Menu #")
        print("#######################")
        print("")
        print("[1] Training Set Errors")
        print("[2] Sample Pool Errors")
        print("")
        print("[b] Back to Main")
        print("[0] Exit")

        ans = input("Enter Action:")

        if ans == "b":
            break
        elif ans == "0":
            sys.exit(0)
        elif ans == "1":
            training_recovery_errors()
        elif ans == "2":
            sample_recovery_errors()


def geometry_optimise():
    global FILE_STRUCTURE

    gjf_dir = FILE_STRUCTURE.get_file_path("ts_gjf")
    gjf_file  = FileTools.get_files_in(gjf_dir, "*.gjf")[0]

    opt_dir = FILE_STRUCTURE.get_file_path("opt")
    FileTools.make_clean_directory(opt_dir)
    FileTools.copy_file(gjf_file, opt_dir)
    new_gjf = FileTools.get_files_in(opt_dir, "*.gjf")[0]

    gjf = GJF_file(new_gjf)

    gjf.optimise()
    gjf.set_default_wfn()
    gjf.write_gjf()

    script_name = "GaussOpt.sh"
    createGaussScript(opt_dir, name=script_name)
    CSFTools.submit_scipt(script_name, exit=True)


def setup_directories():
    global FILE_STRUCTURE

    ts = FILE_STRUCTURE.get_file_path("training_set")
    sp = FILE_STRUCTURE.get_file_path("sample_pool")

    FileTools.make_clean_directory(ts)
    FileTools.make_clean_directory(sp)

    ts_gjf = FILE_STRUCTURE.get_file_path("ts_gjf")
    sp_gjf = FILE_STRUCTURE.get_file_path("sp_gjf")

    FileTools.make_directory(ts_gjf)
    FileTools.make_directory(sp_gjf)


def write_to_csv():
    global FILE_STRUCTURE

    while True:
        print("")
        print("############")
        print("# CSV Menu #")
        print("############")
        print("")
        print("[1] Training Set")
        print("[2] Sample Pool")
        print("")
        print("[b] Back to Main")
        print("[0] Exit")

        ans = input("Select Set:")

        if ans == "b":
            break
        elif ans == "0":
            sys.exit(0)
        elif ans == "1":
            gjfs = FileTools.get_files_in(FILE_STRUCTURE.get_file_path("ts_gjf"), "*.gjf")
            ints = FileTools.get_files_in(FILE_STRUCTURE.get_file_path("ts_aimall"), "*_atomicfiles/")
        elif ans == "2":
            gjfs = FileTools.get_files_in(FILE_STRUCTURE.get_file_path("sp_gjf"), "*.gjf")
            ints = FileTools.get_files_in(FILE_STRUCTURE.get_file_path("sp_aimall"), "*_atomicfiles/")
        
        csv = input("Enter name of CSV: ")
        if not csv.endswith(".csv"):
            csv += ".csv"

        s = Points(gjfs=gjfs, int_directories=ints)
        s.to_csv(csv)
        print("Wrote Set To <ATOM>_%s" % csv)

def get_ts_size():
    global FILE_STRUCTURE
    return len(FileTools.get_files_in(FILE_STRUCTURE.get_file_path("ts_gjf"), "*.gjf"))

def set_ts_size():
    global TRAINING_POINTS_TO_USE
    TRAINING_POINTS_TO_USE = get_ts_size()

def editTrainingPoints():
    global TRAINING_POINTS_TO_USE
    max_ts_size = get_ts_size()
    while True:
        print()
        print("Current training set size: {}".format(TRAINING_POINTS_TO_USE))
        print("Max training set size: {}".format(max_ts_size))
        ans = int(input("Enter new training set size: "))
        if ans > max_ts_size:
            print("Error: Maximum training set size is {}\n"\
                  "You inputted {}, please select a lower "\
                  "number".format(max_ts_size, ans))
            print()
        elif ans <= 0:
            print("Error: Training set size must be a positive, "\
                  "none 0 integer, please enter a new size")
            print()
        else:
            TRAINING_POINTS_TO_USE = ans
            break
            

def get_sp_size():
    global FILE_STRUCTURE
    return len(FileTools.get_files_in(FILE_STRUCTURE.get_file_path("sp_gjf"), "*.gjf"))

def test():
    global FILE_STRUCTURE

    gjfs = FileTools.get_files_in(FILE_STRUCTURE.get_file_path("ts_gjf"), "*.gjf")
    ints = FileTools.get_files_in(FILE_STRUCTURE.get_file_path("ts_aimall"), "*_atomicfiles/")

    ts = Points(gjfs=gjfs, int_directories=ints)

    ts.to_csv("ts.csv")

if __name__ == "__main__":
    defineGlobals()
    readArguments()
    set_ts_size()

    if len(glob("*.sh.*")) > 0:
        os.system("rm *.sh.*")

    if ITERATION == MAX_ITERATION:
        sys.exit(0)

    if AUTO_SUBMISSION_MODE:
        autoRun(submit=False)

    options = {"1_1": submitTrainingGJFs, "1_2": submitTrainingWFNs, "1_3": makeTrainingSets, "1_4": moveIQAModels,
                "1_5": makeMPoleTrainingSets, "1_6": moveMPoleModels, "1_log": moveModelsToLog, "1_e" : editTrainingPoints,
               "2_1": submitSampleGJFs, "2_2": submitSampleWFNs, "2_3": getSampleAIMALLEnergies,
               "4": calculateErrors, "a": autoRun, "del":CSFTools.del_jobs,
               "dlpoly_1": run_DLPOLY_on_LOG, "dlpoly_g": submit_DLPOLY_to_gaussian,
               "dlpoly_wfn": get_DLPOLY_WFN_energies, "dlpoly_edit": edit_DLPOLY,
               "s_1": s_curves, "s_2": recovery_error_menu, "s_format": makeFormattedFiles,
               "t_opt": geometry_optimise, "t_setup": setup_directories, "t_csv": write_to_csv}

    while True:
        if len(glob("*.sh.*")) > 0:
            os.system("rm *.sh.*")

        print("")
        print("##############################")
        print("#          MAIN MENU         #")
        print("# KRIGING TRAINING ASSISTANT #")
        print("##############################")
        print("")
        print("[1] Training Set")
        print("[2] Sample Pool")
        print("[3] Test Set")
        print("[4] Calculate Errors")
        print("")
        print("[a] Auto Run")
        print("")
        print("[b] Backup Data")
        print("[del] Delete Current Running Jobs")
        print("")
        print("[s] Analysis Tools")
        print("[dlpoly] Run DLPOLY on Sample Pool using LOG")
        print("")
        print("[t] Tools")
        print("")
        print("[0] Exit")
        print("Enter action:")
        num = input()
        if num == "1":
            while True:
                print("")
                print("########################")
                print("# 1. Training Set Menu #")
                print("########################")
                print("")
                print("[1] Submit GJFs to Gaussian")
                print("[2] Submit WFNs to AIMALL")
                print("[3] Make IQA Models")
                print("[4] Move IQA Models")
                print("")
                print("[5] Make MPole Models")
                print("[6] Move MPole Models")
                print("")
                print("[log] Move Models to Log")
                print("[e]   Edit Number of Points To Use")
                print("")
                print("Current Training Set Size: %d" % TRAINING_POINTS_TO_USE)
                print("")
                print("[b] Go back")
                print("[0] Exit")
                num += "_" + input()
                if "b" in num.lower():
                    break
                elif num == "1_0":
                    sys.exit()
                else:
                    options[num]()
                    num = "1"
        elif num == "2":
            while True:
                print("")
                print("#######################")
                print("# 2. Sample Pool Menu #")
                print("#######################")
                print("")
                print("[1] Submit GJFs to Gaussian")
                print("[2] Submit WFNs to AIMALL")
                print("[3] Cleanup AIMALL Directory")
                print("")
                print("Current Sample Pool Size: %d" % get_sp_size())
                print("")
                print("[b] Go back")
                print("[0] Exit")
                num += "_" + input()
                if "b" in num.lower():
                    break
                elif num == "2_0":
                    sys.exit()
                else:
                    options[num]()
                    num = "2"
        elif num == "3":
            while True:
                print("")
                print("####################")
                print("# 2. Test Set Menu #")
                print("####################")
                print("")
                print("[1] Submit GJFs to Gaussian")
                print("[2] Submit WFNs to AIMALL")
                print("[3] Cleanup AIMALL Directory")
                print("")
                print("Current Test Set Size: %d" % get_test_size())
                print("")
                print("[b] Go back")
                print("[0] Exit")
                num += "_" + input()
                if "b" in num.lower():
                    break
                elif num == "2_0":
                    sys.exit()
                else:
                    options[num]()
                    num = "2"
        elif num == "dlpoly":
            while True:
                print("")
                print("###############")
                print("# DLPOLY Menu #")
                print("###############")
                print("")
                print("[1] Run DLPOLY using MODELs in LOG")
                print("[2] Run DLPOLY using current MODELs")
                print("")
                print("[g] Calculate Gaussian Energies of DLPOLY run")
                print("")
                print("[wfn] Get All WFN Energies")
                print("[edit] Edit DLPOLY Settings")
                print("")
                print("[b] Go back")
                print("[0] Exit")
                num += "_" + input()
                if "b" in num.lower():
                    break
                elif num == "dlpoly_0":
                    sys.exit()
                else:
                    options[num]()
                    num = "dlpoly"
        elif num == "s":
            while True:
                print("")
                print("#################")
                print("# Analysis Menu #")
                print("#################")
                print("")
                print("[1] Make S-Curves")
                print("[2] Get Recovery Errors")
                print("")
                print("[format] Format")
                print("")
                print("[b] Go back")
                print("[0] Exit")
                num += "_" + input()
                if "b" in num.lower():
                    break
                elif num == "s_0":
                    sys.exit()
                else:
                    options[num]()
                    num = "s"
        elif num == "t":
            while True:
                print("")
                print("##############")
                print("# Tools Menu #")
                print("##############")
                print("")
                print("[opt] Geometry Optimise With Gaussian")
                print("[csv] Write Set to CSV")
                print("[setup] Setup TS and SP Directories")
                print("")
                print("[b] Go back")
                print("[0] Exit")
                num += "_" + input()
                if "b" in num.lower():
                    break
                elif num == "s_0":
                    sys.exit()
                else:
                    options[num]()
                    num = "s"
        elif num == "0":
            sys.exit()
        else:
            options[num]()
