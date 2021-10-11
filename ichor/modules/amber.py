from ichor.machine import Machine
from ichor.modules.modules import Modules

AmberModules = Modules()

AmberModules[Machine.csf3] = [
    "module load apps/intel-17.0/amber/18-at19-may2019",
]
