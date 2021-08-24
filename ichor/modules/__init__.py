""" Defines modules that need to be loaded in submission scripts, so that compute nodes have access to programs such as Gaussian and AIMALL."""

from ichor.modules.aimall import AIMAllModules
from ichor.modules.ferebus import FerebusModules
from ichor.modules.gaussian import GaussianModules
from ichor.modules.modules import Modules
from ichor.modules.python import PythonModules

__all__ = [
    "Modules",
    "FerebusModules",
    "GaussianModules",
    "AIMAllModules",
    "PythonModules",
]
