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

SYSTEM_NAME = "WATER"
ALF = []

AUTO_SUBMISSION_MODE = False
MAX_ITERATION = 0
POINTS_PER_ITERATION = 1

MULTIPLE_ADDITION_MODE = "multiple"

ITERATION = 0
STEP = 0

FORMAT_GJFS = True
POTENTIAL = "B3LYP"
BASIS_SET = "6-31+g(d,p)"

EXIT = False

FILE_STRUCTURE = []
IMPORTANT_FILES = {}

TRAINING_POINTS = []
SAMPLE_POINTS = []

MACHINE = "csf3"

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

    src = None
    prop = re.compile(r"([\w. ]+)\s*=\s*(.*)")

    def __init__(self, source="config.properties"):
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
        return "/".join(list(reversed(file_path[:-1]))) + "/"

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
            bs = "Unkown Basis Function"
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
        self.fname = fname

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
        correlation = np.sum([self.theta_values[h] * (xi[h] - xj[h])**2
                           for h in range(self.nFeats)])
        return np.exp(-correlation)

    def predict(self, x_values):
        predictions = np.empty(shape=(len(x_values)))
        for i in range(len(x_values)):
            r = np.empty(shape=(self.nTrain))
            for j in range(self.nTrain):
                r[j] = self.gaussian_correlation(x_values[i], self.training_data[j])

            predictions[i] = self.mu + np.dot(np.matmul(r.T, self.inv_R), (self.kriging_centres - self.mu))
        
        return predictions

    def variance(self, x_values):
        s_values = np.empty(shape=(len(x_values)))
        ones = np.ones(shape=(self.nTrain))
        res3 = np.dot(np.matmul(ones.T, self.inv_R), ones)
        for i in range(len(x_values)):
            r = np.empty(shape=(self.nTrain))
            for j in range(self.nTrain):
                r[j] = self.gaussian_correlation(x_values[i], self.training_data[j])

                res1 = np.dot(np.matmul(r.T, self.inv_R), r)
                res2 = np.dot(np.matmul(ones.T, self.inv_R), r)

            s_values[i] = self.sigma_squared * (1 - res1 + (1 - res2)**2/res3)

        return s_values

    def calcCVError(self):
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


class Point:

    def __init__(self, fname, point_type="training"):
        global ALF

        self.fname = fname
        self.base_name = self.get_base()
        self.number = re.findall("\d+", self.base_name)[0]
        self.type = point_type.lower()

        self.aimall_directory = self.determineDirectory("aimall")

        coordinate_lines = FileTools.get_files_in(self.fname)
        self.atoms, self.coordinates = FileTools.parse_coordinate_lines(coordinate_lines)
        self.features = calcFeats(ALF, self.coordinates)

        self.cv_error = 0.0
        self.variance = 0.0

        self.error = 0.0

        self.INTs = self.read_INTs()

    def get_base(self):
        return self.fname.split(".")[0]

    def determineDirectory(self, type):
        return 0

    def read_INTs(self):
        global SYSTEM_NAME
        global FILE_STRUCTURE

        INTs = []

        if self.type == "training":
            aimall_dir = FILE_STRUCTURE.get_file_path("ts_aimall")
        elif self.type == "sample":
            aimall_dir = FILE_STRUCTURE.get_file_path("sp_aimall")

        int_files = FileTools.get_files_in("%s*/%s*.int" % (aimall_dir, self.base_name))

        for int_file in int_files:
            INTs.append(INT(int_file))

        return INTs


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

    def get_distance_to(self, reference, atom=-1):
        feat_sum = 0.0
        for i in range(len(self.features)):
            for j in range(len(self.features[i])):
                feat_sum += (self.features[i][j] - reference.features[i][j])**2
        if feat_sum < self.min_distance:
            self.min_distance = feat_sum
            self.cv_error = reference.cv_error
            self.cv_atom = atom


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
        self.modules.append(module)

    def add_job(self, job, options=""):
        self.jobs.append([job, options])

    def change_directory(self, d):
        self.dir = d

    def set_cores(self, cores):
        self.cores = cores

    def add_path(self, path):
        self.path = path

    def get_cores_string(self):
        if self.cores == 1:
            return ""
        elif self.cores < 16:
            return "#$ -pe smp.pe %d\n" % self.cores

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

    def get_job_submission(self, job_num):
        global FILE_STRUCTURE
        """

        :param job_num: the index for self.jobs[]
               job_type: the type of job being executed
        :return: Execution string for the job to be submitted

        You can set the job type by specifying during initialisation or by calling set_type()
        Add custom types by extending the elif statement below
        A default submission has been given if no type is specified
        """
        if self.type == "gaussian":
            return "export PREFERRED_SCDIR=/scratch\n" \
                   "$g09root/g09/g09 %s %s\n" % (self.jobs[job_num][0], self.jobs[job_num][1])
        elif self.type == "aimall":
            return "~/AIMAll/aimqb.ish " \
                   "-nogui -usetwoe=0 -atom=all -encomp=3 -boaq=gs30 -iasmesh=fine -nproc=2 " \
                   "%s >& %s\n" % (self.jobs[job_num][0], self.jobs[job_num][1])
        elif self.type == "ferebus":
            ferebus_loc = FILE_STRUCTURE.get_file_path("programs") + "FEREBUS"
            copy_line = "cp %s %s\n" % (ferebus_loc, self.jobs[job_num][0])
            cd_line = "cd %s\n" % self.jobs[job_num][0]
            while_loop = "while [ ! -f *q11s* ]\n" \
                         "do\n" \
                         "export OMP_NUM_THREADS=$NSLOTS; ./FEREBUS\n" \
                         "done\n"
            return "%s%s%s" % (copy_line, cd_line, while_loop)
        elif self.type == "python":
            return "%s %s %s" % ("python", self.jobs[job_num][0], self.jobs[job_num][1])
        elif self.type == "dlpoly":
            cp_dlpoly_string = "cp %sDLPOLY.Z %s" % (FILE_STRUCTURE.get_file_path("programs"), self.jobs[job_num][0])
            cd_string = "cd %s" % self.jobs[job_num][0]
            execution_string = "export $OMP_NUM_THREADS=%d; ./DLPOLY.Z" % self.cores
            return "%s\n%s\n%s\n" % (cp_dlpoly_string, cd_string, execution_string)
        else:
            return "export $OMP_NUM_THREADS=%d; ./%s %s\n" % (self.cores, self.jobs[job_num][0], self.jobs[job_num][1])

    def add_job_string(self, job_num, jobid):
        if jobid == 0:
            return self.get_job_submission(job_num)
        else:
            job_string = "if [ \"$SGE_TASK_ID\" == \"%d\" ];\n" \
                         "then\n" \
                         "sleep 1\n" % jobid

            # if type(self.dir) == type([]):
            #     job_string += "%s\n" % self.dir[job_num]

            job_string += "%s" \
                          "fi\n\n" % self.get_job_submission(job_num)
            return job_string

    def write_script(self):
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
    def sorted_tuple(data, i, reverse=False):
        return sorted(data, key=lambda tup: tup[i], reverse=reverse)

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

        tree.create_node("DLPOLY", "dlpoly", parent="file_locs")

        tree.create_node("LOG", "log", parent="file_locs")

        tree.create_node("PROGRAMS", "programs", parent="file_locs")

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
                if re.match("\s*\w+(\s+[+-]?\D+){3}", line):
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
            if re.match("\s*\w+(\s+[+-]?\D+){3}", line):
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
        shutil.move(src, dst)

    @staticmethod
    def move_files(src, dst, fileType):
        if not fileType.startswith("."):
            filetype = "." + fileType
        for item in os.listdir(src):
            if item.endswith(fileType):
                pathname = os.path.join(src, item)
                if os.path.isfile(pathname):
                    shutil.move(pathname, dst)

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
        return fname.split(".")[0].split("/")[-1]
      
    @staticmethod
    def cleanup_aimall_dir(aimall_dir):
        all_directories = FileTools.get_directories(aimall_dir)
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

        FileTools.remove_files(aimall_dir, ".extout")
        FileTools.remove_files(aimall_dir, ".mgp")
        FileTools.remove_files(aimall_dir, ".mgpviz")
        FileTools.remove_files(aimall_dir, ".sum")
        FileTools.remove_files(aimall_dir, ".sumviz")
        FileTools.remove_files(aimall_dir, ".wfn")
        FileTools.remove_files(aimall_dir, ".log")

    @staticmethod
    def remove_no_noise(model):
        with open(model, "r") as f:
            data = f.readlines()

        del data[6]

        with open(model, "w") as f:
            f.writelines(data)


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

    def __init__(self, directory,  atoms, number_of_training_points, number_of_steps=500, write_setup_files=True):
        self.directory = directory
        self.number_of_steps = number_of_steps
        self.atoms = atoms
        self.number_of_training_points = number_of_training_points

        if not self.directory.endswith("/"):
            self.directory += "/"

        if write_setup_files:
            self.writeCONTROL()
            self.writeFIELD()
            self.writeKRIGING()

    def writeCONTROL(self):
        global SYSTEM_NAME

        with open(self.directory + "CONTROL", "w+") as o:
            o.write("Title: %s\n" % SYSTEM_NAME)
            o.write("# This is a generic CONTROL file. Please adjust to your requirement.\n")
            o.write("# Directives which are commented are some useful options.\n\n")
            o.write("ensemble nvt hoover 0.02\n")
            o.write("temperature 10.0\n\n")
            o.write("#perform zero temperature run (really set to 10K)\n")
            o.write("zero\n")
            o.write("# optimise distance 0.000001\n\n")
            o.write("# Cap forces during equilibration, in unit kT/angstrom.\n")
            o.write("# (useful if your system is far from equilibrium)\n")
            o.write("cap 100.0\n\n")
            o.write("# Increase array size per domain\n")
            o.write("# densvar 10 %\n\n")
            o.write("# Bypass checking restrictions and reporting\n")
            o.write("#no index\n")
            o.write("#no strict\n")
            o.write("#no topolgy\n")
            o.write("no vdw\n\n")
            o.write("steps %d\n" % self.number_of_steps)
            o.write("equilibration %d\n" % self.number_of_steps)
            o.write("#scale every 2\n")
            o.write("#timestep 0.001\n")
            o.write("timestep 0.001\n\n")
            o.write("cutoff 15.0\n")
            o.write("fflux\n\n")
            o.write("# Need these for bond contraints\n")
            o.write("#mxshak 100\n")
            o.write("#shake 1.0e-6\n\n")
            o.write("# Continue MD simulation\n")
            o.write("#restart\n\n")
            o.write("traj 0 1 2\n")
            o.write("print every 1\n")
            o.write("stats every 1\n")
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

    class Atom:
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
                    atoms.append(Atom(l[0], [float(l[1]), float(l[2]), float(l[3])], n))
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
    ang2bohr = 1.889725989
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

    global SYSTEM_NAME
    global ALF
    global MAX_ITERATION
    global POINTS_PER_ITERATION

    global MULTIPLE_ADDITION_MODE

    FILE_STRUCTURE = FileTools.setup_file_structure()
    IMPORTANT_FILES = FileTools.setup_important_files()

    alf_reference_file = None

    # config reading
    config = ConfigProvider()

    for key, val in config.items():
        if key == "SYSTEM_NAME":
            SYSTEM_NAME = val
        if key == "POINTS_PER_ITERATION":
            POINTS_PER_ITERATION = int(val)
        if key == "ALF":
            ALF = ast.literal_eval(val)
        if key == "ALF_REFERENCE_FILE":
            alf_reference_file = val
        if key == "MAX_ITERATION":
            MAX_ITERATION = int(val)
        if key == "MULTIPLE_ADDITION_MODE":
            MULTIPLE_ADDITION_MODE = val
        if key == "POTENTIAL":
            POTENTIAL = val.upper()
        if key == "BASIS_SET":
            BASIS_SET = val

    # ALF checking
    if not ALF:
        if not alf_reference_file:
            alf_reference_file = FileTools.get_files_in(FILE_STRUCTURE.get_file_path("ts_gjf"), "*.gjf")[0]
        ALF = AtomicLocalFrame(alf_reference_file)
   
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
    if not files:
        gjfs = FileTools.get_files_in(dir, "*.gjf")
    else:
        gjfs = files
    gaussSub = SubmissionScript(name, type="gaussian", cores=2)
    if MACHINE == "csf2":
        gaussSub.add_module("apps/binapps/gaussian/g09b01_em64t")
    if MACHINE == "csf3":
        gaussSub.add_module("apps/binapps/gaussian/g09d01_em64t")
    # gaussSub.change_directory(dir)
    for gjf in gjfs:
        gaussSub.add_job(gjf, options=gjf.replace(".gjf", ".log"))
    gaussSub.write_script()


def formatGJF(fname, coordinates=None):
    global POTENTIAL
    global BASIS_SET

    gjf = GJF(fname, potential=POTENTIAL, basis_set=BASIS_SET)

    #gjf.add_keywords(["6D", "10F", "guess=huckel", "integral=(uncontractaobasis)", "Density=Current"])
    #gjf.gen_basis_set("truncated")

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

    print(all_wfns)

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
        print("All wfns complete\n\n")



def submitTrainingGJFs():
    global FILE_STRUCTURE

    gjf_directory = FILE_STRUCTURE.get_file_path("ts_gjf")
    createGaussScript(gjf_directory)

    if FORMAT_GJFS:
        for gjf in FileTools.get_files_in(gjf_directory, "*.gjf", sorting="natural"):
            formatGJF(gjf)

    CSFTools.submit_scipt("GaussSub.sh", exit=True)


def submitTrainingWFNs():
    global FILE_STRUCTURE
    global POTENTIAL

    gjf_dir = FILE_STRUCTURE.get_file_path("ts_gjf")
    wfn_dir = FILE_STRUCTURE.get_file_path("ts_wfn")
    aimall_dir = FILE_STRUCTURE.get_file_path("ts_aimall")

    checkWFNs(gjf_dir, wfn_dir)

    if len(FileTools.get_files_in(gjf_dir, "*.wfn")) > 0:
        FileTools.make_clean_directory(wfn_dir)
        FileTools.make_clean_directory(aimall_dir)
    else:
        FileTools.make_directory(wfn_dir)
        FileTools.make_directory(aimall_dir)

    FileTools.move_files(gjf_dir, wfn_dir, ".wfn")

    if POTENTIAL == "B3LYP":
        FileTools.add_functional(wfn_dir, POTENTIAL)

    FileTools.copy_files(wfn_dir, aimall_dir, ".wfn")

    FileTools.remove_files(gjf_dir, ".log")

    aimsub = SubmissionScript("AIMSub.sh", type="aimall", cores=2)

    aimsub.add_option(option="-j", value="y")
    aimsub.add_option(option="-o", value="AIMALL.log")
    aimsub.add_option(option="-e", value="AIMALL.err")
    aimsub.add_option(option="-S", value="/bin/bash")

    aimsub.add_path("~/AIMALL")

    wfns = FileTools.get_files_in(aimall_dir, "*.wfn")

    for i in range(len(wfns)):
        wfn = wfns[i]
        job = "%sJOB%d.log" % (aimall_dir, i+1)
        aimsub.add_job(wfn, options=job)

    aimsub.write_script()

    CSFTools.submit_scipt(aimsub.name, exit=True)


def makeTrainingSets():
    global FILE_STRUCTURE
    global AUTO_SUBMISSION_MODE

    gjf_dir = FILE_STRUCTURE.get_file_path("ts_gjf")
    aimall_dir = FILE_STRUCTURE.get_file_path("ts_aimall")

    fereb_dir = FILE_STRUCTURE.get_file_path("ts_ferebus")

    FileTools.make_clean_directory(fereb_dir)
    FileTools.cleanup_aimall_dir(aimall_dir)

    fereSub = SubmissionScript("FERESub.sh", type="ferebus", cores=4)

    if MACHINE == "csf2":
        fereSub.add_module("libs/intel/nag/fortran_mark23_intel")
        fereSub.add_module("compilers/intel/fortran/15.0.3")
        fereSub.add_module("mpi/intel-14.0/openmpi/1.8.3")
        fereSub.add_module("compilers/intel/c/14.0.3")
        fereSub.add_module("mpi/open64-4.5.2.1/openmpi/1.8.3-ib-amd-bd")
    elif MACHINE == "csf3":
        fereSub.add_module("mpi/intel-17.0/openmpi/3.1.3")
        fereSub.add_module("libs/intel/nag/fortran_mark26_intel")

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
        atom_dir = fereb_dir + atom + "/"
        os.mkdir(atom_dir)

        # Read Data From Int Files
        int_files = FileTools.get_files_in(directory, "*.int")
        ints = []
        for int_file in int_files:
            ints.append(INT(int_file))

        training_set_file = atom_dir + atom + "_TRAINING_SET.txt"
        with open(training_set_file, "w+") as f:
            row_count = 1
            for gjf_i, int_i in zip(gjf_data, ints):
                features = gjf_i.get_atom_features(atom)
                formated_features = ["{0:11.8f}".format(i) for i in features]

                features_string = "   ".join(formated_features)

                iqa_terms = []

                iqa_terms.append(str(int_i.IQA_terms["T(A)"]))
                iqa_terms.append(str(int_i.IQA_terms["VC_IQA(A,A')/2"]))
                iqa_terms.append(str(int_i.IQA_terms["VX_IQA(A,A')/2"]))
                iqa_terms.append(str(int_i.IQA_terms["E_IQA(A)"]))
                iqa_terms.append(str(int_i.IQA_terms["E_IQA_Intra(A)"]))
                iqa_terms.append(str(int_i.IQA_terms["E_IQA_Inter(A)"]))

                for i in range(len(iqa_terms), 25):
                    iqa_terms.append("0")

                iqa_string = "   ".join(iqa_terms)
                row_number = str(row_count).zfill(4)

                f.write("%s   %s    " % (features_string, iqa_string) + str(row_count).zfill(4) + "\n")
                row_count += 1
        
        FerebusTools.write_finput(atom_dir, len(atom_directories), atom, len(gjf_data))

        fereSub.add_job(atom_dir)

    fereSub.write_script()

    if not AUTO_SUBMISSION_MODE:
        CSFTools.submit_scipt(fereSub.name, sync=True)
        moveIQAModels()
    else:
        sys.exit(0)


def moveIQAModels():
    global SYSTEM_NAME
    global FILE_STRUCTURE

    ferebus_dir = FILE_STRUCTURE.get_file_path("ts_ferebus")
    atom_directories = FileTools.get_atom_directories(ferebus_dir)

    q11s_files = []
    for atom_directory in atom_directories:
        if not atom_directory.endswith("/"):
            atom_directory += "/"
        q11s_locs = FileTools.get_files_in(atom_directory, "*q11s*.txt")
        if len(q11s_locs) == 1:
            q11s_files.append(q11s_locs[0])

    if len(q11s_files) == len(atom_directories):
        models_dir = FILE_STRUCTURE.get_file_path("ts_models")
        FileTools.make_clean_directory(models_dir)
        for q11s_file in q11s_files:
            q11s_name = q11s_file.split("/")[-1]
            q11s_num = q11s_name.replace(".txt", "").split("_")[-1]
            model_filename = "%s%s_kriging_IQA_%s.txt" % (models_dir, SYSTEM_NAME, q11s_num)
            FileTools.copy_file(q11s_file, model_filename)
            FileTools.remove_no_noise(model_filename)
    else:
        print("Error: IQA Models not complete.")
        exit(1)


def submitSampleGJFs():
    global FILE_STRUCTURE

    gjf_directory = FILE_STRUCTURE.get_file_path("sp_gjf")
    createGaussScript(gjf_directory)

    if FORMAT_GJFS:
        for gjf in FileTools.get_files_in(gjf_directory, "*.gjf", sorting="natural"):
            formatGJF(gjf)

    CSFTools.submit_scipt("GaussSub.sh", exit=True)


def submitSampleWFNs():
    global FILE_STRUCTURE

    gjf_dir = FILE_STRUCTURE.get_file_path("sp_gjf")

    wfn_dir = FILE_STRUCTURE.get_file_path("sp_wfn")
    aimall_dir = FILE_STRUCTURE.get_file_path("sp_aimall")

    checkWFNs(gjf_dir, wfn_dir)

    FileTools.make_clean_directory(wfn_dir)
    FileTools.make_clean_directory(aimall_dir)

    FileTools.move_files(gjf_dir, wfn_dir, ".wfn")

    if POTENTIAL == "B3LYP":
        FileTools.add_functional(wfn_dir, POTENTIAL)

    FileTools.copy_files(wfn_dir, aimall_dir, ".wfn")

    FileTools.remove_files(gjf_dir, ".log")

    aimsub = SubmissionScript("AIMSub.sh", type="aimall", cores=2)

    aimsub.add_option(option="-j", value="y")
    aimsub.add_option(option="-o", value="AIMALL.log")
    aimsub.add_option(option="-e", value="AIMALL.err")
    aimsub.add_option(option="-S", value="/bin/bash")

    aimsub.add_path("~/AIMALL")

    wfns = FileTools.get_files_in(aimall_dir, "*.wfn")

    for i in range(len(wfns)):
        wfn = wfns[i]
        job = "%sJOB%d.log" % (aimall_dir, i+1)
        aimsub.add_job(wfn, options=job)

    aimsub.write_script()

    CSFTools.submit_scipt(aimsub.name, exit=True)


def getSampleAIMALLEnergies():
    global FILE_STRUCTURE
    global IMPORTANT_FILES

    gjf_dir = FILE_STRUCTURE.get_file_path("sp_gjf")
    aimall_dir = FILE_STRUCTURE.get_file_path("sp_aimall")

    FileTools.cleanup_aimall_dir(aimall_dir)
    atom_directories = FileTools.natural_sort(FileTools.get_atom_directories(aimall_dir))

    atoms = []
    int_data = []
    for directory in atom_directories:
        # Find out atom type
        atom = str(directory.split("/")[-1])

        # Read Data From Int Files
        int_files = FileTools.get_files_in(directory, "*.int")
        ints = []
        for int_file in int_files:
            ints.append(INT(int_file))

        atoms.append(atom)
        int_data.append(ints)

    atoms = FileTools.natural_sort(atoms)

    with open(IMPORTANT_FILES["sp_aimall_energies"], "w+") as f:
        f.write("No.,%s,Total\n" % ",".join(atoms))
        for i in range(len(int_data[0])):
            num = re.findall("\d+", int_data[0][i].name)[0]
            e_iqa_values = [0]*3
            total_e_iqa = 0.0
            int_i: INT
            for j in range(len(int_data)):
                e_iqa = int_data[j][i].IQA_terms["E_IQA(A)"]
                total_e_iqa += e_iqa
                e_iqa_values[atoms.index(int_data[j][i].atom)] = e_iqa
            f.write("%s,%s,%f\n" % (num, ",".join(map(str,e_iqa_values)), total_e_iqa))


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
                sample_geometry.get_distance_to(training_geometries[i], atom=i)

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
    for i in range(len(cv_errors)):
        EPE.append((i, calcEPE(cv_errors[i], variance[i], alpha)))
    
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

    training_gjf_dir = FILE_STRUCTURE.get_file_path("ts_gjf")
    training_wfn_dir = FILE_STRUCTURE.get_file_path("ts_wfn")
    training_aimall_dir = FILE_STRUCTURE.get_file_path("ts_aimall")
    training_atom_directories = FileTools.get_atom_directories(training_aimall_dir)
    training_atom_directories = FileTools.natural_sort(training_atom_directories)
    training_set_size = len(FileTools.get_files_in(training_gjf_dir, "*.gjf", sorting="none"))

    log_dir = FILE_STRUCTURE.get_file_path("log")
    if first_iteration:
        FileTools.make_clean_directory(log_dir)
    model_dir = "%s%s%s" % (log_dir, SYSTEM_NAME, str(training_set_size).zfill(4))
    os.mkdir(model_dir)
    FileTools.copy_files(FILE_STRUCTURE.get_file_path("ts_models"), model_dir, ".txt")

    sample_gjf_dir = FILE_STRUCTURE.get_file_path("sp_gjf")
    sample_gjfs = FileTools.get_files_in(sample_gjf_dir, "*.gjf", sorting="natural")

    sample_wfn_dir = FILE_STRUCTURE.get_file_path("sp_wfn")
    sample_wfns = FileTools.get_files_in(sample_wfn_dir, "*.wfn", sorting="natural")

    sample_aimall_dir = FILE_STRUCTURE.get_file_path("sp_aimall")
    sample_atom_directories = FileTools.get_atom_directories(sample_aimall_dir)
    sample_atom_directories = FileTools.natural_sort(sample_atom_directories)

    for i in range(len(MEPE)):
        index = MEPE[i][0]
        print(index)

        sample_gjf = sample_gjfs[index]
        training_gjf = "%s%s%s.gjf" % (training_gjf_dir, SYSTEM_NAME, str(training_set_size + i + 1).zfill(4))
        FileTools.move_file(sample_gjf, training_gjf)
        print("Moved %s to %s" % (sample_gjf, training_gjf))

        sample_wfn = sample_wfns[index]
        training_wfn = "%s%s%s.wfn" % (training_wfn_dir, SYSTEM_NAME, str(training_set_size + i + 1).zfill(4))
        FileTools.move_file(sample_wfn, training_wfn)
        print("Moved %s to %s" % (sample_wfn, training_wfn))

        print("")
        for j in range(len(sample_atom_directories)):
            sample_atom_directory = sample_atom_directories[j]
            training_atom_directory = training_atom_directories[j]

            atom = sample_atom_directory.split("/")[-1]

            sample_aimalls = FileTools.get_files_in(sample_atom_directory + "/", "*.int")
            sample_aimall = sample_aimalls[index]
            training_aimall = "%s/%s%s_%s.int" % (training_atom_directory, SYSTEM_NAME,
                                                  str(training_set_size + i + 1).zfill(4), atom.lower())
            FileTools.move_file(sample_aimall, training_aimall)
            print("Moved %s to %s" % (sample_aimall, training_aimall))

        with open(IMPORTANT_FILES["sp_aimall_energies"], "r") as f:
            data = f.readlines()

        aimall_data = data[index+1]
        del data[index+1]

        with open(IMPORTANT_FILES["sp_aimall_energies"], "w+") as f:
            f.writelines(data)

        print("Deleted line %d from AIMALL_Energies.csv" % (index+1))

        e_iqa = float(aimall_data.split(",")[-1])
        Etrue = (e_iqa - predictions[index])**2

        with open("ErrorFile.csv", "a") as f:
            f.write("%s,%.10f,%.10f,%.10f,%.10f\n" % (str(index+1).zfill(4), Etrue, cv_errors[index], variance[index],
                                                      alpha))
        print("")


def runDLPOLYOnLOG():
    dlpoly_base_dir = FILE_STRUCTURE.get_file_path("dlpoly")
    FileTools.make_clean_directory(dlpoly_base_dir)

    log_dir = FILE_STRUCTURE.get_file_path("log")
    model_dirs = FileTools.get_files_in(log_dir, "*/")

    sample_gjf_dir = FILE_STRUCTURE.get_file_path("sp_gjf")
    sample_gjfs = FileTools.get_files_in(sample_gjf_dir, "*.gjf")
    gjf_file = sample_gjfs[0]

    atoms = UsefulTools.get_atoms()

    dlpolysub = SubmissionScript("DLPOLYsub.sh", type="dlpoly")

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
        ans = input("Would you like to wait for DLPOLY to complete and calculate\n"
                    "Gaussian Energy from optimised structure?[Y/N]")

        if ans.upper() in  ["Y", "N", "YES", "NO"]:
            break
        else:
            print("%s not a valid answer\n" % ans)

    ans = ans.upper()

    if ans in ["Y", "YES"]:
        CSFTools.submit_scipt(dlpolysub.name, sync=True)
    else:
        CSFTools.submit_scipt(dlpolysub.name, exit=True)

    dlpoly_gjf_dir = dlpoly_base_dir + "GJF/"
    os.mkdir(dlpoly_gjf_dir)

    for dlpoly_directory in dlpoly_working_directories:
        coordinates = FileTools.get_last_coordinates(dlpoly_directory + "TRAJECTORY.xyz")

        model_name = dlpoly_directory.rstrip("/").split("/")[-1]

        gjf_fname = dlpoly_gjf_dir + model_name + ".gjf"
        gjf = formatGJF(gjf_fname, coordinates=coordinates)

    createGaussScript(dlpoly_gjf_dir, name="DLPOLYGaussSub.sh")
    CSFTools.submit_scipt("DLPOLYGaussSub.sh", sync=True)

    wfns = FileTools.get_files_in(dlpoly_gjf_dir, "*.wfn", sorting="natural")
    with open(dlpoly_base_dir + "Energies.txt", "w+") as o:
        for wfn in wfns:
            with open(wfn, "r") as f:
                last_line = f.readlines()[-1]

            wfn_energy = re.findall("[+-]?\d+.\d+", last_line)[0]

            o.write("%s\n" % wfn_energy)


def autoRun(submit=True):
    global MAX_ITERATION
    global STEP

    pJID = None
    if submit:
        jid = open("jid.txt", "w+")
        for i in range(MAX_ITERATION):
            pysub = SubmissionScript("pysub.sge", type="python")
            pysub.add_option(option="-N", value=sys.argv[0])
            pysub.add_option(option="-S", value="/bin/bash")
            pysub.add_option(option="-o", value="outputfile.log")
            pysub.add_option(option="-j", value="y")
            pysub.add_job(sys.argv[0], "-a -i %d -s %d" % (i, 0))
            pysub.write_script()

            if pJID:
                pJID = CSFTools.submit_scipt(pysub.name, hold_jid=pJID, return_jid=True)
            else:
                pJID = CSFTools.submit_scipt(pysub.name, return_jid=True)

            print("Submitted %s\t\tjid:%s" % (pysub.name, pJID))
            jid.write("%s\n" % pJID)

            fereSub = SubmissionScript("FERESub.sh", type="ferebus", cores=4)

            if MACHINE == "csf2":
                fereSub.add_module("libs/intel/nag/fortran_mark23_intel")
                fereSub.add_module("compilers/intel/fortran/15.0.3")
                fereSub.add_module("mpi/intel-14.0/openmpi/1.8.3")
                fereSub.add_module("compilers/intel/c/14.0.3")
                fereSub.add_module("mpi/open64-4.5.2.1/openmpi/1.8.3-ib-amd-bd")
            elif MACHINE == "csf3":
                fereSub.add_module("mpi/intel-17.0/openmpi/3.1.3")
                fereSub.add_module("libs/intel/nag/fortran_mark26_intel")

            fereb_dir = FILE_STRUCTURE.get_file_path("ts_ferebus")
            aimall_dir = FILE_STRUCTURE.get_file_path("ts_aimall")
            atom_directories = FileTools.natural_sort(FileTools.get_atom_directories(aimall_dir))
            for directory in atom_directories:
                atom_dir = "%s%s/" % (fereb_dir, directory.split("/")[-1])
                fereSub.add_job(atom_dir)
            fereSub.write_script()

            pJID = CSFTools.submit_scipt(fereSub.name, hold_jid=pJID, return_jid=True)
            jid.write("%s\n" % pJID)

            print("Submitted %s\t\tjid:%s" % (fereSub.name, pJID))

            pysub = SubmissionScript("pysub.sge", type="python")
            pysub.add_option(option="-N", value=sys.argv[0])
            pysub.add_option(option="-S", value="/bin/bash")
            pysub.add_option(option="-o", value="outputfile.log")
            pysub.add_option(option="-j", value="y")
            pysub.add_job(sys.argv[0], "-a -i %d -s %d" % (i, 1))
            pysub.write_script()

            pJID = CSFTools.submit_scipt(pysub.name, hold_jid=pJID, return_jid=True)
            jid.write("%s\n" % pJID)

            print("Submitted %s\t\tjid:%s" % (pysub.name, pJID))
        jid.close()
    else:
        if STEP == 0:
            makeTrainingSets()
        else:
            moveIQAModels()
            calculateErrors()

    sys.exit(0)


if __name__ == "__main__":
    defineGlobals()
    readArguments()

    if len(glob("*.sh.*")) > 0:
        os.system("rm *.sh.*")

    if ITERATION == MAX_ITERATION:
        sys.exit(0)

    if AUTO_SUBMISSION_MODE:
        autoRun(submit=False)

    options = {"1_1": submitTrainingGJFs, "1_2": submitTrainingWFNs, "1_3": makeTrainingSets, "1_4": moveIQAModels,
               "2_1": submitSampleGJFs, "2_2": submitSampleWFNs, "2_3": getSampleAIMALLEnergies,
               "3": calculateErrors, "4": runDLPOLYOnLOG, "a": autoRun, "d":CSFTools.del_jobs}

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
        print("[3] Calculate Errors")
        print("[4] Run DLPOLY on Sample Pool using LOG")
        print("")
        print("[a] Auto Run")
        print("")
        print("[b] Backup Data")
        print("[d] Delete Current Running Jobs")
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
                print("[3] Make Models")
                print("[4] Move IQA Models")
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
                print("[3] Get AIMALL Energies")
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
        elif num == "0":
            sys.exit()
        else:
            options[num]()

