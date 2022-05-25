from ichor.ichor_hpc import MACHINE
from ichor.modules.modules import Modules

InternetModules = Modules()

InternetModules[Machine.csf3] = ["tools/env/proxy"]
