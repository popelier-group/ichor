from ichor.ichor_hpc.batch_system.machine_setup import Machine
from ichor.modules.modules import Modules

AIMAllModules = Modules()

AIMAllModules[Machine.ffluxlab] = [
    "apps/aimall/19.02.13",
]
