from pathlib import Path
from typing import Union

import pandas as pd

from ichor.core.files.file import FileContents, ReadFile


class DlPolyFFLUX(ReadFile):
    """READS the FFLUX file from FFLUX.

    :param path: Path to FFLUX file

    :ivar df: A pandas dataframe storing all the data in the FFLUX file.
    :ivar sum_iqa_energy: The total energies array of shape ntimesteps
    :ivar vdw_energy: The Van der Waals energies of each timestep. Only computed
        if there are multiple molecules. Otherwise they will be 0.0
    :ivar electrostatic_energy: The electrostatic energies of each timestep. Only computed
        if there are multiple molecules. Otherwise they will be 0.0
    """

    def __init__(self, path: Union[Path, str]):

        super().__init__(path)
        self.df = FileContents

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.stem == "FFLUX"

    def _read_file(self):

        self.df = pd.read_csv(
            self.path,
            skiprows=2,
            index_col=0,
            header=None,
            sep=r"\s+",
            names=["step", "E_IQA/Ha", "E_vdW/kJ mol-1", "E_coul/kJ mol-1"],
        )

    @property
    def sum_iqa_energy(self):
        return self.df["E_IQA/Ha"].values

    @property
    def vdw_energy(self):
        return self.df["E_vdW/kJ mol-1"].values

    @property
    def electrostatic_energy(self):
        return self.df["E_coul/kJ mol-1"].values
