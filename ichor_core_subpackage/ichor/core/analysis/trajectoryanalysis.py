from ichor.core.files import Trajectory, DlpolyHistory, XYZ, GJF
from ichor.core.files.file import ReadFile
from ichor.core.calculators import default_connectivity_calculator
from scipy.spatial.distance import cdist
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from typing import Union, List, Tuple, Iterator, Iterable
import itertools


def pairwise(iterable: Iterable) -> Iterator[Tuple[int,int]] :    
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


class TrajectoryAnalysis(ReadFile):
    """TrajectoryAnalysis is a class used for general analysis of 
    molecular dynamics trajectories. 
    """    
    def __init__(self, trajectory_path: Union[Path, str]):
        """__init__ 

        :param trajectory_path: Path to the trajectory file. Can be an xyz or a DLPOLY4 trajectory.
        :type trajectory_path: Union[Path, str]
        """        
        ReadFile.__init__(self, trajectory_path)
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
        """distances_matrix is a property that returns a distance matrix of 
        all timesteps of a trajectory

        :return: matrix of shape (timesteps,natoms,natoms)
        """                 
        if self._distances_matrix is None:
            self._compute_distances_matrix()
        return self._distances_matrix

    def _compute_distances_matrix(self):
        """_compute_distances_matrix computes the matrix of distances of 
        all timesteps of a trajectory using cdists
        """
        self._distances_matrix = np.zeros(
            (len(self.trajectory), self.trajectory.natoms, self.trajectory.natoms)
        )
        for i, t in enumerate(self.trajectory):
            self._distances_matrix[i, :, :] = cdist(t.coordinates, t.coordinates)

    def delta_dirac(self, r0: float, r1: float) -> int:
        """delta_dirac function to compute a modified version of the Dirac delta function. 
        In other words this uses the distances_matrix attribute and checks
        all the distances that are between two int values.
        This is mainly used to compute the distribution of distances h(r).

        :param r0: lower bound of the interval
        :param r1: higher bound of the interval
        :return: number of values that are within that interval
        """                
        #Index is a f
        index = (r0 < self.distances_matrix) & (self.distances_matrix < r1)
        true_vals = len(index[index == True])
        return true_vals

    @property
    def distance_hist(self) -> List[float]:
        """distance_hist attribute which returns the bins to plot
        an histogram 

        :return: list of floats
        """        
        return self.distributions

    @property
    def bins(self) -> List[float]:
        """bins _summary_

        :return: _description_
        """        
        return self.r

    def hr(self, nbins=1000, max_dist=10.0):
        self.r = np.linspace(0.0, max_dist, nbins)
        # round_distances_matrix = np.round(self.distances_matrix,decimals=decimals)
        for pair in pairwise(self.r):
            distribution = self.delta_dirac(pair[0], pair[1])
            self.distributions.append(
                distribution
                / (
                    len(self.trajectory)
                    / (self.trajectory.natoms * (self.trajectory.natoms - 1))
                )
            )

    def plot_hr(self, save_path: Union[Path, str]):
        fig, ax = plt.subplots(figsize=(12, 6))
        # ax.hist(self.r-1, bins=len(self.r)-1, weights=self.distributions)
        # ax.stairs(self.distributions, self.r)
        ax.plot(self.r[:-1], self.distributions)
        fig.savefig(save_path, dpi=300)


class Stability(TrajectoryAnalysis):
    def __init__(
        self,
        reference_path: Union[Path, str],
        trajectory_path: Union[Path, str],
        threshold: float,
    ):
        TrajectoryAnalysis.__init__(self, trajectory_path)
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

        def _read_file(self):
            self.reference._read_file()

    @property
    def bond_lengths_matrix(self):
        if self._bond_lengths_matrix is None:
            self._compute_bond_lengths_matrix()
        return self._bond_lengths_matrix

    def _compute_bond_lengths_matrix(self):
        self._bond_lengths_matrix = np.zeros_like(self.distances_matrix)
        # mask = connectivity[np.newaxis, ...].repeat(self.distances_matrix.shape[0], axis=0)
        distances_matrix_masked = np.where(
            self.connectivity_ref, self.distances_matrix, 0
        )
        self._bond_lengths_matrix = distances_matrix_masked

    def bond_lengths_differences_matrix(self):
        reference_distance_matrix = cdist(
            self.reference.coordinates, self.reference.coordinates
        )
        reference_distance_matrix_masked = np.where(
            self.connectivity_ref, reference_distance_matrix, 0
        )
        diff = (
            self.bond_lengths_matrix
            - reference_distance_matrix_masked[np.newaxis, :, :]
        )
        # print(np.abs(diff))
        # Now creating a mask matrix where all the differences of distances that are above a threshold return 1 while the rest is 0
        mask = np.where(np.abs(diff) > self.threshold, 1, 0)
        return mask

    def stable_trajectory(self):
        mask = self.bond_lengths_differences_matrix()
        # indices where the trajectory is unstable above the threshold value
        indices = np.nonzero(mask)
        if indices is not None:
            print(
                f"Timestep {indices[0][0]} has bonds over the threshold thus deemed UNSTABLE!"
            )
        else:
            print(f"Trajectory is fully stable for {self.trajectory.shape[0]} steps")
        self.trajectory = self.trajectory[: indices[0][0]]


t = TrajectoryAnalysis(Path("toluene.xyz"))
stab = Stability(Path("toluene_single.xyz"),Path("HISTORY_toluene_8ktrain"), threshold=0.5)
#stab = TrajectoryAnalysis(Path("HISTORY_toluene_8ktrain"))
# stab.hr()
# stab.plot_hr("./hist_8k_paracetamol_unstable.png")
stab.stable_trajectory()
stab.hr()
t.hr()
#fig, ax = plt.subplots(figsize=(12, 6))
#ax.plot(t.bins[:-1], t.distance_hist, label="MD17")
#ax.plot(stab.bins[:-1], stab.distance_hist, label="FFLUX_8ktrain")
#plt.legend()
#fig.savefig("./TOLUENE_comparison_hist_8k_vs_MD17_stable.png", dpi=300)
quit()
