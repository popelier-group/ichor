"""Implements an Enum for atomic distances to decrease the chance of spelling mistakes / typos."""
# TODO: potenitally move to constants as this will not change. Ones less file to worry about.
from enum import Enum


class AtomicDistance(Enum):
    Bohr = "bohr"
    Angstroms = "angstroms"
