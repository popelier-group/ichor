from ichor.hpc.machine import Machine
from ichor.hpc.modules.modules import Modules

FerebusModules = Modules()


FerebusModules[Machine.csf3] = [
    "compilers/intel/18.0.3",
]

FerebusModules[Machine.csf4] = [
    "iomkl/2020.02",
]

FerebusModules[Machine.ffluxlab] = [
    "compilers/intel/20.0.1",
]
