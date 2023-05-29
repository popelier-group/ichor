import numpy as np
from ichor.core.files.directory import AnnotatedDirectory
from ichor.core.files.dl_poly import (
    DlPolyFFLUX,
    DlpolyHistory,
    DlPolyIQAEnergies,
    DlPolyIQAForces,
)
from ichor.core.files.optional_file import OptionalFile, OptionalPath


class FFLUXDirectory(AnnotatedDirectory):
    """READS a FFLUX Directory containing FFLUX, IQA_ENERGIES, IQA_FORCEs
    and HISTORY file

    :param path: Path to FFLUX Directory
    """

    fflux_file: OptionalPath[DlPolyFFLUX] = OptionalFile
    iqa_energies_file: OptionalPath[DlPolyIQAEnergies] = OptionalFile
    iqa_forces_file: OptionalPath[DlPolyIQAForces] = OptionalFile
    history_file: OptionalPath[DlpolyHistory] = OptionalFile

    @property
    def iqa_energies(self) -> np.ndarray:
        """Returns individual atom iqa enegy array of shape ntimesteps x natoms"""
        return self.iqa_energies_file.energies

    @property
    def total_iqa_energies(self) -> np.ndarray:
        """Returns total energy array of shape ntimesteps"""
        return self.fflux_file.sum_iqa_energy

    @property
    def iqa_forces(self) -> np.ndarray:
        """Returns iqa forces array of shape ntimesteps x natoms x 3"""
        return self.iqa_forces_file.forces

    @property
    def natoms(self) -> int:
        """Returns number of atoms"""
        return self.history_file.natoms

    @property
    def coordinates(self) -> np.ndarray:
        """Returns coordinates as array of shape ntimesteps x natoms x 3"""
        return self.history_file.coordinates
