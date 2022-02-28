from pathlib import Path
from typing import List, Optional

from ichor.batch_system import JobID
from ichor.main.aimall import submit_points_directory_to_aimall
from ichor.main.pandora import submit_points_directory_to_morfi
from ichor.qct import (QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM,
                       QuantumChemicalTopologyProgram)


class CannotSubmitPointsDirectoryToQuantumChemicalTopologyProgram(
    Exception
):  # might as well carry on the tradition
    def __init__(self, directory: Path, qctp: QuantumChemicalTopologyProgram):
        self.message = f"{directory} not submitted to QCTP ({qctp}), need to write function to submit"


def submit_qct(
    directory: Path, atoms: Optional[List[str]] = None, force: bool = False
) -> Optional[JobID]:
    qctp = QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM()
    if qctp is QuantumChemicalTopologyProgram.AIMAll:
        qctpf = submit_points_directory_to_aimall
    elif qctp is QuantumChemicalTopologyProgram.Morfi:
        qctpf = submit_points_directory_to_morfi
    else:
        raise CannotSubmitPointsDirectoryToQuantumChemicalTopologyProgram(
            directory, qctp
        )
    return qctpf(directory, atoms=atoms, force=force)
