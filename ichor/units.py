"""Implements an Enum for atomic distances to decrease the chance of spelling mistakes / typos."""
# matt_todo: potentially move to constants as this will not change. Ones less file to worry about.
from enum import Enum


class AtomicDistance(Enum):
    """ Enum that encapsulates units that are used in ICHOR."""
    Bohr = "bohr"
    Angstroms = "angstroms"
