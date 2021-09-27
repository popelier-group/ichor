from ichor.machine import Machine
from ichor.modules.modules import Modules

PandoraModules = Modules()

PandoraModules[Machine.ffluxlab] = ["libs/python/pyscf/1.7.4"]
