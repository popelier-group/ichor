import random
import warnings
from pathlib import Path
from typing import Union

import numpy as np
from ichor.core.files import PointsDirectory, Trajectory
from ichor.core.files.dl_poly import DlPolyFFLUX, DlpolyHistory
from matplotlib import pyplot as plt

try:
    import scienceplots  # noqa

    plt.style.use("science")
except ImportError:
    warnings.warn("Could not import scienceplots. Will not use scienceplots styles.")


def get_random_geometries_from_fflux_simulation(
    history: Union[DlpolyHistory, Path, str],
    k: int = 1000,
    fflux_file: Union[DlPolyFFLUX, Path, str] = None,
):
    """Gets random geometries from fflux simulation, so that the true energy from Gaussian
    can be computed from the geometries.
    This function writes out several files.
    1. New trajectory containing random geometries to be submitted to Gaussian.
    2. A txt file containing the indices of the random geometries taken from the HISTORY
    3. If a FFLUX file is given, it writes out a .npy file containing the predicted
        total energy associated with the random geometries. If not give, the user can use
        the .txt file and obtain the energies from the FFLUX file themselves.

    :param history: A HISTORY file or path to HISTORY file containing FFLUX geometries
    :param k: How many geometries to get from the HISTORY, defaults to 1000
    :param fflux_file: A FFLUX file where to get the total predicted energies
        associated with the HISTORY file, defaults to None.
        If given, this will write out a .npy file containing predicted
        total energies array. If not given, it will not write out the
        np array.
    """

    if isinstance(history, (Path, str)):
        history = DlpolyHistory(history)

    random_indices = random.sample(range(len(history)), k=1000)

    new_trajetory = Trajectory(f"{k}_random_geometries_from_fflux_simulation.xyz")
    with open(f"{k}_random_indices_from_trajectory.txt", "w") as writef:
        for r in random_indices:
            writef.write(f"{r}\n")
            new_trajetory.append(history[r])

    new_trajetory.write()

    if fflux_file:
        if isinstance(fflux_file, (Path, str)):
            fflux_file = DlPolyFFLUX(fflux_file)

        total_energies = fflux_file.total_energy[random_indices]

        np.save(
            f"{k}_total_predicted_energies_from_simulation_hartree.npy", total_energies
        )


def plot_true_vs_predicted_from_arrays(
    predicted_energies_array_hartree: np.ndarray,
    true_energies_array_hartree: Union[np.ndarray, PointsDirectory],
    title: str = "",
    subtract_mean: bool = False,
    absolute_diff: bool = True,
):
    """Plots true vs predicted energies, as well as calculates R^2 value

    :param predicted_energies_array_hartree: np array containing FFLUX predicted energies
        In hartrees
    :param true_energies_array_hartree: a np.array cotaning true energies (in hartrees)
        or a PointsDirectory (containing ordered wfns from which to get the array) again
        in Hartrees
    :param title: The title of the plot, defaults to ""
    :param subtract_mean: Whether to subtract mean of data, defaults to False
    :param absolute_diff: Whether to use the absolute of the differences
        of true and predicted or not, defaults to True
    """

    from sklearn.metrics import r2_score

    if isinstance(true_energies_array_hartree, PointsDirectory):
        true_energies = []
        pd = true_energies_array_hartree
        for p in pd:
            true_energies.append(p.wfn.total_energy)
        true_energies_array_hartree = np.array(true_energies)
    else:
        true_energies_array_hartree = true_energies_array_hartree

    diff = (predicted_energies_array_hartree - true_energies_array_hartree) * 2625.5

    r_score = r2_score(true_energies_array_hartree, predicted_energies_array_hartree)

    with open("min_max_r2.txt", "w") as writef:

        writef.write(f"Maximum absolute difference: {np.max(np.abs(diff))}\n")
        writef.write(f"Minimum absolute difference: {np.min(np.abs(diff))}\n")
        writef.write(f"R^2 score: {r_score}")

    if subtract_mean:
        mean = true_energies_array_hartree.mean()
        true_energies_array_hartree = true_energies_array_hartree - mean
        predicted_energies_array_hartree = predicted_energies_array_hartree - mean

    if absolute_diff:
        diff = np.abs(diff)

    fig, ax = plt.subplots(figsize=(9, 9))
    # c is the array of differences, cmap is for the cmap to use
    scatter_object = ax.scatter(
        true_energies_array_hartree,
        predicted_energies_array_hartree,
        c=diff,
        cmap="viridis",
    )

    p1 = max(max(predicted_energies_array_hartree), max(true_energies_array_hartree))
    p2 = min(min(predicted_energies_array_hartree), min(true_energies_array_hartree))
    plt.plot([p1, p2], [p1, p2], "k--", linewidth=2.0, alpha=0.5)

    # Show the major grid and style it slightly.
    ax.grid(which="major", color="#DDDDDD", linewidth=1.2)
    ax.grid(True)

    # note that there will be a warning that no axes need legends, that is fine
    # make legend have a frame
    # the fonsize in the legend is for text apart from the title
    # set it to some reasonable value so that the frame is large enough to fit title
    leg = plt.legend(
        facecolor="white", framealpha=1, frameon=True, fontsize=14, loc="lower right"
    )
    # set title as the R^2 value
    leg.set_title(f"R$^2$ = {r_score:.3f}", prop={"size": 20})

    if title:
        ax.set_title(title, fontsize=28)

    ax.set_xlabel("True Energy / Ha", fontsize=24)
    ax.set_ylabel("Predicted Energy / Ha", fontsize=24)

    # colorbar for difference in energies
    cbar = fig.colorbar(scatter_object)
    if absolute_diff:
        cbar.set_label("Absolute Difference / kJ mol$^{-1}$", fontsize=24)
    else:
        cbar.set_label("Difference / kJ mol$^{-1}$", fontsize=24)

    ax.ticklabel_format(axis="both", style="plain", useOffset=False)
    ax.tick_params(axis="both", which="major", labelsize=18)
    plt.show()
