from ichor.hpc.machine import Machine
from ichor.hpc.modules.modules import Modules

CP2KModules = Modules()

CP2KModules[Machine.ffluxlab] = [
    "apps/cp2k/6.1.0",
]
CP2KModules[Machine.csf3] = ["apps/binapps/cp2k/6.1.0"]
CP2KModules[Machine.csf4] = ["cp2k/6.1-iomkl-2020.02"]
