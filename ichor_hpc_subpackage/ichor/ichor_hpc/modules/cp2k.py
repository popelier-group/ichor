from ichor.ichor_hpc.machine_setup.machine_setup import Machine
from ichor.modules.modules import Modules

CP2KModules = Modules()

CP2KModules[Machine.ffluxlab] = [
    "apps/cp2k/6.1.0",
]
CP2KModules[Machine.csf3] = ["apps/binapps/cp2k/6.1.0"]
