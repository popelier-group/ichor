from ichor.hpc.machine import Machine
from ichor.hpc.modules.modules import Modules

DlpolyModules = Modules()


DlpolyModules[Machine.csf3] = [
    "compilers/intel/18.0.3",
]


DlpolyModules[Machine.ffluxlab] = [
    "mpi/intel/18.0.3",
]
