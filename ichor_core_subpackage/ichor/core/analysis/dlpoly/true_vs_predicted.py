import random
import warnings
from pathlib import Path
from typing import List, Union

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
    true_energies_array_hartree: Union[np.ndarray, List[PointsDirectory]],
    absolute_diff: bool = True,
    filename="output.svg",
):
    """Plots true vs predicted energies, as well as calculates R^2 value

    :param predicted_energies_array_hartree: np array containing FFLUX predicted energies
        In hartrees
    :param true_energies_array_hartree: a np.array cotaning true energies (in hartrees)
        or a PointsDirectory (containing ordered wfns from which to get the array) again
        in Hartrees
    :param title: The title of the plot, defaults to ""
    :param absolute_diff: Whether to use the absolute of the differences
        of true and predicted or not, defaults to True
    """

    from sklearn.metrics import r2_score

    if isinstance(true_energies_array_hartree[0], PointsDirectory):
        all_true_energies = []
        for pd in true_energies_array_hartree:
            one_system_energies = []
            for p in pd:
                one_system_energies.append(p.wfn.total_energy)
            all_true_energies.append(one_system_energies)
        true_energies_array_hartree = np.array(all_true_energies)
    else:
        true_energies_array_hartree = true_energies_array_hartree

    nsystems = predicted_energies_array_hartree.shape[0]

    diff = (predicted_energies_array_hartree - true_energies_array_hartree) * 2625.5

    r2_scores = [
        r2_score(true_energies_array_hartree[i], predicted_energies_array_hartree[i])
        for i in range(nsystems)
    ]

    with open("min_max_r2.txt", "w") as writef:

        for i, d in enumerate(diff):

            writef.write(f"Maximum absolute difference {i}: {np.max(np.abs(d))}\n")
            writef.write(f"Minimum absolute difference {i}: {np.min(np.abs(d))}\n")
            writef.write(f"R^2 score {i}: {r2_scores[i]}\n")

    if absolute_diff:
        diff = np.abs(diff)

    fig, axes = plt.subplots(1, nsystems, figsize=(30 * nsystems, 15))
    # c is the array of differences, cmap is for the cmap to use
    if not isinstance(axes, np.ndarray):
        axes = [axes]

    for i, ax in enumerate(axes):

        scatter_object = ax.scatter(
            true_energies_array_hartree[i],
            predicted_energies_array_hartree[i],
            c=diff[i],
            cmap="viridis",
            s=200,
        )

        p1 = max(
            max(predicted_energies_array_hartree[i]),
            max(true_energies_array_hartree[i]),
        )
        p2 = min(
            min(predicted_energies_array_hartree[i]),
            min(true_energies_array_hartree[i]),
        )
        ax.plot([p1, p2], [p1, p2], "k--", linewidth=3.0, alpha=0.5)

        steps = np.linspace(p2, p1, 5)
        steps = np.around(steps, 3)
        ax.set_xticks(steps)
        ax.set_xticklabels(steps)
        ax.set_yticks(steps)
        ax.set_yticklabels(steps)

        ax.tick_params(axis="both", which="major", labelsize=48, pad=15)
        ax.tick_params(axis="both", which="minor", labelsize=48, pad=15)

        # Show the major grid and style it slightly.
        ax.grid(which="major", color="#DDDDDD", linewidth=4.0)
        ax.grid(True)

        # note that there will be a warning that no axes need legends, that is fine
        # make legend have a frame
        # the fonsize in the legend is for text apart from the title
        # set it to some reasonable value so that the frame is large enough to fit title
        leg = ax.legend(
            facecolor="white",
            framealpha=1,
            frameon=True,
            fontsize=0.1,
            loc="lower right",
            borderpad=15.0,
        )
        # set title as the R^2 value
        leg.set_title(f"R$^2$ = {r2_scores[i]:.3f}", prop={"size": 54})
        leg.get_frame().set_linewidth(3.0)

        ax.set_xlabel("True Energy / Ha", fontsize=54, labelpad=20)
        ax.set_ylabel("Predicted Energy / Ha", fontsize=54, labelpad=20)

        # colorbar for difference in energies
        cbar = fig.colorbar(scatter_object)
        if absolute_diff:
            cbar.set_label(
                "Absolute Difference / kJ mol$^{-1}$", fontsize=54, labelpad=20
            )
        else:
            cbar.set_label("Difference / kJ mol$^{-1}$", fontsize=54, labelpad=20)
        cbar.ax.tick_params(labelsize=48, pad=15)

        # ax.ticklabel_format(axis="both", style="plain", useOffset=False)

        # ax.yaxis.set_major_formatter(FormatStrFormatter('%.3f'))
        # ax.xaxis.set_major_formatter(FormatStrFormatter('%.3f'))

    fig.savefig(filename, pad_inches=0.2)

    return fig, axes
