from enum import Enum
from ichor.globals.machine import Machine


class NodeType(Enum):
    LoginNode = 'login'
    ComputeNode = 'compute'
