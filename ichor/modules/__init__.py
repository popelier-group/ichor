from ichor.modules.aimall import AIMAllModules
from ichor.modules.ferebus import FerebusModules
from ichor.modules.gaussian import GaussianModules
from ichor.modules.modules import Modules
from ichor.modules.python import PythonModules
from ichor.modules.internet import InternetModules
from ichor.common.functools import run_once

import os
import re
import subprocess
from pathlib import Path
from typing import List, Union

MODULES_HOME = Path("/usr/share/Modules")


@run_once
def initialise_modules():
    global MODULES_HOME

    from ichor.globals import GLOBALS, Machine

    if GLOBALS.MACHINE is Machine.csf3:
        MODULES_HOME = Path("/opt/clusterware/opt/modules")

    if 'MODULEPATH' not in os.environ:
        f = open(MODULES_HOME / "init/.modulespath", "r")
        path = []
        for line in f.readlines():
            line = re.sub("#.*$", '', line)
            if line is not '':
                path.append(line)
        os.environ['MODULEPATH'] = os.pathsep.join(path)

    if not 'LOADEDMODULES' in os.environ:
        os.environ['LOADEDMODULES'] = ''


def module(*args):
    if type(args[0]) == type([]):
        args = args[0]
    else:
        args = list(args)
    output, error = subprocess.Popen([f'{MODULES_HOME}/bin/modulecmd', 'python'] +
                                     args, stdout=subprocess.PIPE).communicate()
    exec(output)


def load_module(module_to_load: Union[str, List[str], Modules]):
    if isinstance(module_to_load, str):
        module('load', module_to_load)
    elif isinstance(module_to_load, list):
        module('load', *module_to_load)
    elif isinstance(module_to_load, Modules):
        from ichor.globals import GLOBALS
        load_module(module_to_load[GLOBALS.MACHINE])
    else:
        raise TypeError(f"Unknown module type: {type(module_to_load)}")


__all__ = [
    "Modules",
    "FerebusModules",
    "GaussianModules",
    "AIMAllModules",
    "PythonModules",
    "InternetModules",
    "load_module"
]
