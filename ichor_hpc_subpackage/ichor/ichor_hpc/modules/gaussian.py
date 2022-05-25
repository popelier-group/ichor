from ichor.ichor_hpc.machine_setup.machine_setup import Machine
from ichor.modules.modules import Modules

GaussianModules = Modules()


GaussianModules[Machine.csf3] = [
    "apps/binapps/gaussian/g09d01_em64t",
]


GaussianModules[Machine.ffluxlab] = [
    "apps/gaussian/g09",
]

GaussianModules[Machine.local] = [
    "test/gaussian/module",
]
