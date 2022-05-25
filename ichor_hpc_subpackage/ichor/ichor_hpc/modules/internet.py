from ichor.ichor_hpc.batch_system.machine_setup import Machine
from ichor.modules.modules import Modules

InternetModules = Modules()

InternetModules[Machine.csf3] = ["tools/env/proxy"]
