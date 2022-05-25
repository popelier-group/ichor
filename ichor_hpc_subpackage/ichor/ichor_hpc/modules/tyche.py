from ichor.ichor_hpc import MACHINE
from ichor.modules.modules import Modules

TycheModules = Modules()

TycheModules[Machine.ffluxlab] = ["compilers/intel/18.0.3"]
TycheModules[Machine.csf3] = ["compilers/intel/18.0.3"]
