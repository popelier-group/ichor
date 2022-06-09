import os
import re
import subprocess
from pathlib import Path
from typing import List, Union

from ichor.core.common.functools import run_once
from ichor.hpc.modules.aimall import AIMAllModules
from ichor.hpc.modules.amber import AmberModules
from ichor.hpc.modules.cp2k import CP2KModules
from ichor.hpc.modules.dlpoly import DlpolyModules
from ichor.hpc.modules.ferebus import FerebusModules
from ichor.hpc.modules.gaussian import GaussianModules
from ichor.hpc.modules.internet import InternetModules
from ichor.hpc.modules.modules import Modules
from ichor.hpc.modules.pandora import MorfiModules, PandoraModules
from ichor.hpc.modules.python import PythonModules
from ichor.hpc.modules.tyche import TycheModules

MODULES_HOME = Path("/usr/share/Modules")


@run_once
def initialise_modules():
    global MODULES_HOME

    from ichor.hpc import MACHINE, Machine

    if MACHINE is Machine.csf3:
        MODULES_HOME = Path("/opt/clusterware/opt/modules")

    if "MODULEPATH" not in os.environ:
        f = open(MODULES_HOME / "init/.modulespath", "r")
        path = []
        for line in f.readlines():
            line = re.sub("#.*$", "", line)
            if line != "":
                path.append(line)
        os.environ["MODULEPATH"] = os.pathsep.join(path)

    if not "LOADEDMODULES" in os.environ:
        os.environ["LOADEDMODULES"] = ""


def module(*args):
    from ichor.hpc import MACHINE, Machine

    if MACHINE is Machine.local:
        return
    if type(args[0]) == type([]):
        args = args[0]
    else:
        args = list(args)
    output, error = subprocess.Popen(
        [f"{MODULES_HOME}/bin/modulecmd", "python"] + args,
        stdout=subprocess.PIPE,
    ).communicate()
    exec(output)


def load_module(module_to_load: Union[str, List[str], Modules]):
    if isinstance(module_to_load, str):
        module("load", module_to_load)
    elif isinstance(module_to_load, list):
        module("load", *module_to_load)
    elif isinstance(module_to_load, Modules):
        from ichor.hpc import MACHINE

        load_module(module_to_load[MACHINE])
    else:
        raise TypeError(f"Unknown module type: {type(module_to_load)}")


__all__ = [
    "Modules",
    "FerebusModules",
    "GaussianModules",
    "AIMAllModules",
    "PythonModules",
    "InternetModules",
    "DlpolyModules",
    "PandoraModules",
    "MorfiModules",
    "AmberModules",
    "CP2KModules",
    "TycheModules",
    "load_module",
]
