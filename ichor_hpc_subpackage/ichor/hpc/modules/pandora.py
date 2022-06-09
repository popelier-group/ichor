from ichor.hpc.machine import Machine
from ichor.hpc.modules.modules import Modules

PandoraModules = Modules()

PandoraModules[Machine.ffluxlab] = ["libs/python/pyscf/1.7.4"]

MorfiModules = Modules()
MorfiModules[Machine.ffluxlab] = ["compilers/intel/18.0.3"]
MorfiModules[Machine.csf3] = ["mpi/intel-18.0/openmpi/4.0.1"]
