from ichor.hpc.machine import Machine
from ichor.hpc.modules.modules import Modules

AIMAllModules = Modules()

AIMAllModules[Machine.ffluxlab] = [
    "apps/aimall/19.02.13",
]
