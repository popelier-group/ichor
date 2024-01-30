from pathlib import Path
from typing import List, Union

import numpy as np

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

    _filetype = ""

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
    def total_energy(self):
        return self.sum_iqa_energy

    @property
    def total_energy_kj_mol(self):
        return self.total_energy * 2625.5

    @property
    def vdw_energy(self):
        return self.df["E_vdW/kJ mol-1"].values

    @property
    def electrostatic_energy(self):
        return self.df["E_coul/kJ mol-1"].values

    @property
    def ntimesteps(self):
        return len(self.total_energy)

    @property
    def delta_between_timesteps(self) -> List[float]:
        """Calculates the delta energy (in kJ mol-1) between
        each pairs of timesteps. Useful for checking convergence of energy
        when doing optimizations.

        :return: List containing the first index (timestep) where the threshold is met
            as well as the list of differences for all timesteps
        """

        differences = []

        for i in range(1, self.ntimesteps):
            differences.append(self.total_energy[i] - self.total_energy[i - 1])

        differences = np.array(differences)

        return differences

    @property
    def delta_between_timesteps_kj_mol(self) -> List[float]:
        """Calculates the delta energy (in kJ mol-1) between
        each pairs of timesteps. Useful for checking convergence of energy
        when doing optimizations.

        :return: List containing the first index (timestep) where the threshold is met
            as well as the list of differences for all timesteps
        """

        return 2625.5 * self.delta_between_timesteps

    def first_index_where_delta_less_than(self, delta=1e-4) -> int:
        """Returns first index where the energy between timesteps is
        below delta (in kJ mol-1)

        :param delta: The threshold when geometry is converged, defaults to 1e-4 kJ mol-1
        """

        diffs = np.abs(self.delta_between_timesteps_kj_mol)

        (indices,) = np.where(diffs < delta)
        idx = indices[0]

        return idx

    # TODO: move to analysis
    def plot_abs_differences(self, until_converged_energy=True):

        from matplotlib import pyplot as plt

        idx = self.first_index_where_delta_less_than()

        if until_converged_energy:
            final_energy = self.delta_between_timesteps_kj_mol[idx]
            plt.plot(
                range(idx), self.delta_between_timesteps_kj_mol[:idx] - final_energy
            )
        else:
            plt.plot(range(self.ntimesteps), self.delta_between_timesteps_kj_mol)

        plt.xlabel("Timestep")
        plt.ylabel("Energy / kJ mol$^{-1}$")

        plt.show()
