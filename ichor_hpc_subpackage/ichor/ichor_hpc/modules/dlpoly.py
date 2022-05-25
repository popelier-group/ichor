from ichor.ichor_hpc.batch_system.machine_setup import Machine
from ichor.modules.modules import Modules

DlpolyModules = Modules()


DlpolyModules[Machine.csf3] = [
    "compilers/intel/18.0.3",
]


DlpolyModules[Machine.ffluxlab] = [
    "mpi/intel/18.0.3",
]
