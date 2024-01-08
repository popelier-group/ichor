from ichor.hpc.machine import Machine
from ichor.hpc.modules.modules import Modules

OrcaModules = Modules()


OrcaModules[Machine.csf3] = [
    "apps/binapps/orca/5.0.3",
]

OrcaModules[Machine.csf4] = [
    "orca/5.0.4-gompi-2021a",
]

OrcaModules[Machine.local] = [
    "test/gaussian/module",
]
