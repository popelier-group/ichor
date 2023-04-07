import os
import re
import subprocess
from pathlib import Path
from typing import List, Union

import ichor.hpc.modules.modules_home
from ichor.core.common.functools import run_once
from ichor.hpc import MACHINE
from ichor.hpc.machine import Machine
from ichor.hpc.modules.modules import Modules


@run_once
def initialise_modules():

    if MACHINE is Machine.csf3:
        ichor.hpc.modules.modules_home.MODULES_HOME = Path(
            "/opt/clusterware/opt/modules"
        )

    if "MODULEPATH" not in os.environ:
        f = open(ichor.hpc.modules.modules_home.MODULES_HOME / "init/.modulespath", "r")
        path = []
        for line in f.readlines():
            line = re.sub("#.*$", "", line)
            if line != "":
                path.append(line)
        os.environ["MODULEPATH"] = os.pathsep.join(path)

    if "LOADEDMODULES" not in os.environ:
        os.environ["LOADEDMODULES"] = ""


def module(*args):

    if MACHINE is Machine.local:
        return
    if isinstance(args[0], list):
        args = args[0]
    else:
        args = list(args)
    output, _ = subprocess.Popen(  # output, error
        [f"{ichor.hpc.modules.modules_home.MODULES_HOME}/bin/modulecmd", "python"]
        + args,
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
