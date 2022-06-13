from ichor.hpc.machine import Machine
from ichor.hpc.modules.modules import Modules

PythonModules = Modules()

PythonModules[Machine.csf3] = ["apps/anaconda3/5.2.0/bin"]

PythonModules[Machine.csf4] = ["anaconda3/2020.07"]

PythonModules[Machine.ffluxlab] = ["apps/anaconda3/3.7.6"]
