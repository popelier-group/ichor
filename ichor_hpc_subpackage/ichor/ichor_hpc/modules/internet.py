from ichor.ichor_hpc.machine_setup.machine import Machine
from ichor.modules.modules import Modules

InternetModules = Modules()

InternetModules[Machine.csf3] = ["tools/env/proxy"]
