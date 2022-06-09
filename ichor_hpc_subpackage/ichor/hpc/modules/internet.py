from ichor.hpc.machine import Machine
from ichor.hpc.modules.modules import Modules

InternetModules = Modules()

InternetModules[Machine.csf3] = ["tools/env/proxy"]
