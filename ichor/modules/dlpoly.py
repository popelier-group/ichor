from ichor.machine import Machine
from ichor.modules.modules import Modules

DlpolyModules = Modules()


DlpolyModules[Machine.csf3] = [
    "compilers/intel/18.0.3",
]


DlpolyModules[Machine.ffluxlab] = [
    "compilers/intel/20.0.1",
]
