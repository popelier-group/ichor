from pathlib import Path
from typing import Optional

from ichor.hpc.batch_system import JobID
from ichor.hpc.main.gaussian import submit_points_directory_to_gaussian
from ichor.hpc.main.pandora import submit_points_directory_to_pyscf
from ichor.hpc.programs.qcp import QUANTUM_CHEMISTRY_PROGRAM, QuantumChemistryProgram


class CannotSubmitPointsDirectoryToQuantumChemistryProgram(
    Exception
):  # lol that name was longer than expected
    def __init__(self, directory: Path, qcp: QuantumChemistryProgram):
        self.message = f"{directory} not submitted to QCP ({qcp}), need to write function to submit"


def submit_qcp(directory: Path, force: bool = False) -> Optional[JobID]:
    qcp = QUANTUM_CHEMISTRY_PROGRAM()

    if qcp is QuantumChemistryProgram.Gaussian:
        qcpf = submit_points_directory_to_gaussian
    elif qcp is QuantumChemistryProgram.PySCF:
        qcpf = submit_points_directory_to_pyscf
    else:
        raise CannotSubmitPointsDirectoryToQuantumChemistryProgram(
            directory, qcp
        )
    return qcpf(directory, force=force)
