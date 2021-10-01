from pathlib import Path
from typing import Optional

from ichor.batch_system import JobID
from ichor.main.gaussian import submit_points_directory_to_gaussian
from ichor.main.pandora import submit_points_directory_to_pyscf
from ichor.qcp import QUANTUM_CHEMISTRY_PROGRAM, QuantumChemistryProgram


class CannotSubmitPointsDirectoryToQuantumChemistryProgram(
    Exception
):  # lol that name was longer than expected
    def __init__(self, directory: Path, qcp: QuantumChemistryProgram):
        self.message = f"{directory} not submitted to QCP ({qcp}), need to write function to submit"


def submit_qcp(directory: Path) -> Optional[JobID]:
    qcp = QUANTUM_CHEMISTRY_PROGRAM()
    if qcp is QuantumChemistryProgram.Gaussian:
        return submit_points_directory_to_gaussian(directory)
    elif qcp is QuantumChemistryProgram.PySCF:
        return submit_points_directory_to_pyscf(directory)
    else:
        raise CannotSubmitPointsDirectoryToQuantumChemistryProgram(
            directory, qcp
        )
