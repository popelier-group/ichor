from ichor.hpc.machine import Machine
from ichor.hpc.modules.modules import Modules

DlpolyModules = Modules()


DlpolyModules[Machine.csf3] = [
    "compilers/intel/18.0.3",
]

DlpolyModules[Machine.csf4] = [
    "iomkl/2020.02",
]

DlpolyModules[Machine.ffluxlab] = [
    "mpi/intel/18.0.3",
]
