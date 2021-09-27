from pathlib import Path

from ichor.batch_system import JobID
from ichor.main.submit_gjfs import submit_gjfs
from ichor.qcp import QUANTUM_CHEMISTRY_PROGRAM, QuantumChemistryProgram

# from ichor.main.sub


def submit_qcp(directory: Path) -> JobID:
    if QUANTUM_CHEMISTRY_PROGRAM is QuantumChemistryProgram.Gaussian:
        return submit_gjfs(directory)
    elif QUANTUM_CHEMISTRY_PROGRAM is QuantumChemistryProgram.PySCF:
        # return submit_pandora(directory)
        pass
