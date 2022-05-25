from ichor.ichor_hpc import MACHINE
from ichor.modules.modules import Modules

AIMAllModules = Modules()

AIMAllModules[Machine.ffluxlab] = [
    "apps/aimall/19.02.13",
]
