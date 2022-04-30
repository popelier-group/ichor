from ichor.ichor_lib.common.types import Enum
from ichor.qcp import QUANTUM_CHEMISTRY_PROGRAM, QuantumChemistryProgram


class QuantumChemicalTopologyProgram(Enum):
    AIMAll = QuantumChemistryProgram.Gaussian
    Morfi = QuantumChemistryProgram.PySCF


def QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM() -> QuantumChemicalTopologyProgram:
    """Returns Enum element of the QCT Program that is going to be used, depending on which Quantum Chemistry Program was used (either Gaussian or PySCF).

    :return: `QuantumChemicalTopologyProgram.AIMALL` or `QuantumChemicalTopologyProgram.Morfi`, depending on the Quantum Chemistry Program that was used.
    """
    return QuantumChemicalTopologyProgram(QUANTUM_CHEMISTRY_PROGRAM())


def ADD_DISPERSION() -> bool:
    """Returns if dispersion is to be added to IQA energies calculated by AIMALL.

    :return: `True` if dispersion is to be added to IQA energies or `False` if dispersion should not be added to IQA energies.
    """
    from ichor.globals import GLOBALS

    return (
        QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM()
        is QuantumChemicalTopologyProgram.Morfi
        and GLOBALS.ADD_DISPERSION_TO_IQA
    )
