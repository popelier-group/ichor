from ichor.common.types import Enum
from ichor.qcp import QUANTUM_CHEMISTRY_PROGRAM, QuantumChemistryProgram


class QuantumChemicalTopologyProgram(Enum):
    AIMAll = QuantumChemistryProgram.Gaussian
    Morfi = QuantumChemistryProgram.PySCF


QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM = QuantumChemicalTopologyProgram(QUANTUM_CHEMISTRY_PROGRAM)
