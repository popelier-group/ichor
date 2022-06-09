"""Implements an Enum for atomic distances to decrease the chance of spelling mistakes / typos."""
# todo: implement conversions between units
from enum import Enum

import numpy as np


class AtomicDistance(Enum):
    """Enum that encapsulates units that are used in ICHOR."""

    Bohr = "bohr"
    Angstroms = "angstroms"


class Angle(Enum):
    Radians = "rad"
    Degrees = "deg"


class Temperature(Enum):
    Kelvin = "K"
    Celsius = "C"


def radians_to_degrees(a):
    return 180 * a / np.pi


def degrees_to_radians(a):
    return np.pi * a / 180
