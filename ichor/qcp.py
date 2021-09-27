from typing import List, Type

from ichor.common.str import in_sensitive
from ichor.common.types import Enum
from ichor.constants import GAUSSIAN_METHODS
from ichor.files import GJF, PandoraInput, QuantumChemistryProgramInput
from ichor.globals import GLOBALS


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


QUANTUM_CHEMISTRY_PROGRAM = QuantumChemistryProgram(GLOBALS.METHOD)
