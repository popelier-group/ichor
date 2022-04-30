from ichor.ichor_hpc.machine_setup.machine.machine import Machine
from ichor.modules.modules import Modules

AIMAllModules = Modules()

AIMAllModules[Machine.ffluxlab] = [
    "apps/aimall/19.02.13",
]
