from ichor.ichor_hpc.machine_setup.machine_setup import Machine
from ichor.modules.modules import Modules

AIMAllModules = Modules()

AIMAllModules[Machine.ffluxlab] = [
    "apps/aimall/19.02.13",
]
