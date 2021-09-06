"""Implements an Enum for atomic distances to decrease the chance of spelling mistakes / typos."""
# todo: implement conversions between units
from enum import Enum


class AtomicDistance(Enum):
    """Enum that encapsulates units that are used in ICHOR."""

    Bohr = "bohr"
    Angstroms = "angstroms"
