from ichor.common.types import Enum
from ichor.qcp import QUANTUM_CHEMISTRY_PROGRAM, QuantumChemistryProgram


class QuantumChemicalTopologyProgram(Enum):
    AIMAll = QuantumChemistryProgram.Gaussian
    Morfi = QuantumChemistryProgram.PySCF


def QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM():
    return QuantumChemicalTopologyProgram(QUANTUM_CHEMISTRY_PROGRAM)
