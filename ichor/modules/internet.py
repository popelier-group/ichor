from ichor.globals.machine import Machine
from ichor.modules.modules import Modules

InternetModules = Modules()

InternetModules[Machine.csf3] = ["tools/env/proxy"]
