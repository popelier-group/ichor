from typing import List, Type

from ichor.core.common.str import in_sensitive
from ichor.core.common.types import Enum
from ichor.core.common.constants import GAUSSIAN_METHODS
from ichor.core.files import GJF, PandoraInput, QuantumChemistryProgramInput
from ichor.hpc import GLOBALS


class MethodNotFound(Exception):
    def __init__(self, method):
        self.message = f"Method {method} not defined by any of {QuantumChemistryProgram.names}"


class QuantumChemistryInputNotFound(Exception):
    def __init__(self, qcp_input):
        self.message = f"Quantum Chemistry Input '{qcp_input.__name__}' not defined by any of {QuantumChemistryProgram.names}"


class QuantumChemistryProgram(Enum):
    PySCF = ["CCSD"], PandoraInput
    Gaussian = GAUSSIAN_METHODS, GJF

    def __init__(self, methods: List[str], input_file: Type):
        self.methods = methods
        self.input_file = input_file

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for item in cls:
                if in_sensitive(value, item.methods):
                    return item
            raise MethodNotFound(value)
        elif isinstance(value, QuantumChemistryProgramInput):
            for item in cls:
                if value is cls.value:
                    return item
            raise QuantumChemistryInputNotFound(value)
        return super()._missing_(value)


def QUANTUM_CHEMISTRY_PROGRAM():
    return QuantumChemistryProgram(GLOBALS.METHOD)
