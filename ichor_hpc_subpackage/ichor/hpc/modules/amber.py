from ichor.hpc.machine import Machine
from ichor.hpc.modules.modules import Modules

AmberModules = Modules()

AmberModules[Machine.csf3] = [
    "apps/intel-17.0/amber/18-at19-may2019",
]

AmberModules[Machine.ffluxlab] = [
    "apps/amber/18-at19",
]
