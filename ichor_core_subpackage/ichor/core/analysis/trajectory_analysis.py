from pathlib import Path
from typing import List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
from ichor.core.calculators import default_connectivity_calculator
from ichor.core.common.pairwise import pairwise
from ichor.core.files import DlpolyHistory, GJF, Trajectory, XYZ
from ichor.core.files.file import ReadFile

# TODO: potentially move Distance to outside of models/kernels
from ichor.core.models.kernels.distance import Distance


class TrajectoryAnalysis(ReadFile):
    """TrajectoryAnalysis is a class used for general analysis of
    molecular dynamics trajectories.
    Functionality for now comprehends only distribution of distances for a single molecule

    :param trajectory_path: Path to the trajectory file. Can be an xyz or a DLPOLY4 trajectory.
    :type trajectory_path: Union[Path, str]

    Example usage:

    .. code-block:: text

        traj = TrajectoryAnalysis('path/to/trajectory')
        traj.hr(nbins=1000,max_dist=10.0)
        traj.plot_hr('path/to/figure.png')
    """

    filetype = ".xyz"

    def __init__(self, trajectory_path: Union[Path, str]):
        ReadFile.__init__(self, trajectory_path)
        trajectory_path = Path(trajectory_path)
        self.trajectory = (
            Trajectory(trajectory_path)
            if trajectory_path.suffix == ".xyz"
            else DlpolyHistory(trajectory_path)
        )
        self._distances_matrix = None
        self._bond_lengths_matrix = None
        self.distributions = []
        self.r = []

    def _read_file(self):
        self.trajectory._read_file()

    @property
    def distances_matrix(self) -> np.ndarray:
        """
        Returns a distance matrix of all timesteps of a trajectory

        :return: matrix of shape (timesteps, natoms, natoms)
        """
        if self._distances_matrix is None:
            self._compute_distances_matrix()
        return self._distances_matrix

    @property
    def distance_hist(self) -> List[float]:
        """
        The bins to plot on a histogram

        :return: The bins to plot
        """
        return self.distributions

    @property
    def bins(self) -> List[float]:
        """
        bins attribute which returns

        :return: _description_
        """
        return self.r

    def _compute_distances_matrix(self):
        """
        Computes the distance matrix between atoms for each timestep and stores
        into the self._distances_matrix attribute for later usage.
        """
        self._distances_matrix = np.zeros(
            (len(self.trajectory), self.trajectory.natoms, self.trajectory.natoms)
        )
        for i, t in enumerate(self.trajectory):
            self._distances_matrix[i, :, :] = Distance.euclidean_distance(
                t.coordinates, t.coordinates
            )

    def delta_dirac(self, r0: float, r1: float) -> int:
        """
        Computes a modified version of the Dirac delta function.
        In other words this uses the distances_matrix attribute and checks
        all the distances that are between two int values.
        This is mainly used to compute the distribution of distances h(r).

        :param r0: lower bound of the interval
        :param r1: higher bound of the interval
        :return: number of values that are within that interval
        """
        index = (r0 < self.distances_matrix) & (self.distances_matrix < r1)
        true_vals = len(index[index is True])
        return true_vals

    def hr(self, nbins: Optional[int] = 1000, max_dist: Optional[float] = 10.0):
        """
        Computes the distributions of distances of all pair-wise distances
        across a whole trajectory.
        This function needs to be called if the bins and distance_hist attributes need to be computed

        :param nbins: number of bins to consider for the distance range considered, defaults to 1000
        :param max_dist: maximum distance to consider for the distribution, defaults to 10.0
        """
        self.r = np.linspace(0.0, max_dist, nbins)
        for pair in pairwise(self.r):
            distribution = self.delta_dirac(pair[0], pair[1])
            self.distributions.append(
                distribution
                / (
                    len(self.trajectory)
                    * (self.trajectory.natoms * (self.trajectory.natoms - 1))
                )
            )

    def plot_hr(self, save_path: Union[Path, str]):
        """Helper function which plots a quick graph for visualising the hr distribution.

        :param save_path: path and name of the file ending in .png
        """
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(self.r[:-1], self.distributions)
        fig.savefig(save_path, dpi=300)


class Stability(TrajectoryAnalysis):
    """
    Class used to check whether a simulation of a molecule is stable given a threshold value.
    Each connected bond distance is subtracted to a reference bond distance
    (e.g. of the corresponding optimised molecule) and then checked against the threshold.

    :param reference_path: path to the reference structure of a molecule. Can be .gjf or .xyz file.
    :param trajectory_path: path to the trajectory file. Can be a DLPOLY4 trajectory or a .xyz trajectory file.
    :param threshold: threshold value for stability across the trajectory.

    Example usage:

    .. code-block:: text

        traj = Stability('path/to/reference.xyz','path/to/trajectory.xyz', threshold=0.5)
        traj.stable_trajectory()
        traj.hr(nbins=1000, max_dist=10.0)
        traj.plot_hr('path/to/figure.png')
    """

    def __init__(
        self,
        reference_path: Union[Path, str],
        trajectory_path: Union[Path, str],
        threshold: float,
    ):
        super().__init__(trajectory_path)
        reference_path = Path(reference_path)
        self.reference = (
            XYZ(reference_path)
            if reference_path.suffix == ".xyz"
            else GJF(reference_path)
        )
        self._bond_lengths_matrix = None
        self.threshold = threshold
        self.connectivity_ref = self.reference.connectivity(
            default_connectivity_calculator
        )

    @property
    def bond_lengths_matrix(self) -> np.ndarray:
        """
        Returns a distances matrix only for bonds.

        :return: numpy array of (timesteps,natoms,natoms) dimensions
        """
        if self._bond_lengths_matrix is None:
            self._compute_bond_lengths_matrix()
        return self._bond_lengths_matrix

    def _compute_bond_lengths_matrix(self):
        """
        Computes a distance matrix of all distances along a trajectory and masks it with
        the connectivity of the reference geometry.
        """
        self._bond_lengths_matrix = np.zeros_like(self.distances_matrix)
        # mask = connectivity[np.newaxis, ...].repeat(self.distances_matrix.shape[0], axis=0)
        distances_matrix_masked = np.where(
            self.connectivity_ref, self.distances_matrix, 0
        )
        self._bond_lengths_matrix = distances_matrix_masked

    def bond_lengths_differences_matrix(self) -> np.ndarray:
        """
        Computes a matrix of the differences of distances
        between a reference geometry and all the timesteps of a trajectory.

        :return: numpy array of dimensions (timesteps,natoms,natoms)
        """
        reference_distance_matrix = Distance.euclidean_distance(
            self.reference.coordinates, self.reference.coordinates
        )
        reference_distance_matrix_masked = np.where(
            self.connectivity_ref, reference_distance_matrix, 0
        )
        diff = (
            self.bond_lengths_matrix
            - reference_distance_matrix_masked[np.newaxis, :, :]
        )
        # Now creating a mask matrix where all the differences of distances
        # that are above a threshold return 1 while the rest is 0
        mask = np.where(np.abs(diff) > self.threshold, 1, 0)
        return mask

    def stable_trajectory(self):
        """
        Computes the bond_lengths_differences_matrix and then checks
        at which timesteps the trajectory is not stable and overwrites the original
        trajectory attribute with the stable trajectory only so that the distribution of distances
        hr can then be computed on the stable part of the trajectory.
        """
        mask = self.bond_lengths_differences_matrix()
        # indices where the trajectory is unstable above the threshold value
        indices = np.nonzero(mask)
        if indices[0].any():
            print(
                f"Timestep {indices[0][0]} has bonds over the threshold! Trajectory is unstable after this."
            )
            self.trajectory = self.trajectory[: indices[0][0]]
        else:
            print(f"Trajectory is fully stable for {len(self.trajectory)} steps")
