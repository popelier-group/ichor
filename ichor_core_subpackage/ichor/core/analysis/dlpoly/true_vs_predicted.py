import random
import warnings
from pathlib import Path
from typing import List, Union

import matplotlib

import numpy as np
from ichor.core.files import PointsDirectory, Trajectory
from ichor.core.files.dl_poly import DlPolyFFLUX, DlpolyHistory
from matplotlib import pyplot as plt

try:
    import scienceplots  # noqa

    plt.style.use("science")

    matplotlib.rcParams.update(
        {
            "text.usetex": False,
            "font.family": "sans-serif",
            "font.serif": "DejaVu Serif",
            "axes.formatter.use_mathtext": False,
            "mathtext.fontset": "dejavusans",
        }
    )
    # matplotlib.rcParams['mathtext.rm'] = 'DejaVu Serif'
    # matplotlib.rcParams['mathtext.it'] = 'DejaVu Serif:italic'
    # matplotlib.rcParams['mathtext.bf'] = 'DejaVu Serif:bold'

except ImportError:
    warnings.warn("Could not import scienceplots. Will not use scienceplots styles.")


from string import ascii_uppercase

ascii_uppercase = list(ascii_uppercase)


def r2_score(true, predicted):

    ssr = np.sum((true - predicted) ** 2)
    true_mean = np.mean(true)
    sst = np.sum((true - true_mean) ** 2)

    return 1 - (ssr / sst)


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
    FIGURE_LABEL_SIZE=48,
    X_Y_LABELS_FONTSIZE=48,
    TICKLABELS_FONTSIZE=30,
    LABELPAD=15.0,
    AXES_PADDING=10.0,
    LINEWIDTH=2.0,
    MAJOR_TICK_LENGTH=6.0,
    MINOR_TICK_LENGTH=3.0,
    LEGEND_BORDERPAD=15.0,
    LEGEND_FRAME_WIDTH=2.0,
    COLORBAR_PADDING=5.0,
    PAD_INCHES=0.05,
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
    :param FIGURE_LABEL_SIZE: The label size of the figures (A, B, C, etc.), defaults to 48
    :param X_Y_LABELS_FONTSIZE: The size of the x and y axis labels, defaults to 48
    :param TICKLABELS_FONTSIZE: The fontsize of the ticklabels, defaults to 30
    :param LABELPAD: The padding of the x y labels from plot, defaults to 15.0
    :param AXES_PADDING: The padding of axes numbers from plot, defaults to 10.0
    :param LINEWIDTH: The width of lines, defaults to 2.0
    :param MAJOR_TICK_LENGTH: The width of major tickmarks, defaults to 6.0
    :param MINOR_TICK_LENGTH: The width of minor tickmarks, defaults to 3.0
    :param LEGEND_BORDERPAD: The border padding of the legend, defaults to 15.0
    :param LEGEND_FRAME_WIDTH: The width of the legend frame, defaults to 2.0
    :param COLORBAR_PADDING: The padding of the colorbar axes, defaults to 5.0
    :param PAD_INCHES: padding on the sides (as tight layout is used), defaults to 0.05
    :param filename: The filename. Note the extension affects the format of the file
        , defaults to "output.svg"
    """

    nsystems = predicted_energies_array_hartree.shape[0]
    WIDTH = 19 * nsystems
    HEIGHT = WIDTH / 4

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

    fig, axes = plt.subplots(1, nsystems, figsize=(WIDTH, HEIGHT), sharey="col")
    # c is the array of differences, cmap is for the cmap to use
    if not isinstance(axes, np.ndarray):
        axes = [axes]

    # only set y label on first axes
    axes[0].set_ylabel(
        "Predicted Energy / Ha",
        fontsize=X_Y_LABELS_FONTSIZE,
        labelpad=LABELPAD,
        fontweight="bold",
    )

    for i, ax in enumerate(axes):

        scatter_object = ax.scatter(
            true_energies_array_hartree[i],
            predicted_energies_array_hartree[i],
            c=diff[i],
            cmap="viridis",
            s=200,
        )

        ax.text(
            0.1,
            0.85,
            rf"$\bf{{{ascii_uppercase[i]}}}$",
            fontsize=FIGURE_LABEL_SIZE,
            transform=ax.transAxes,
        )

        p1 = max(
            max(predicted_energies_array_hartree[i]),
            max(true_energies_array_hartree[i]),
        )
        p2 = min(
            min(predicted_energies_array_hartree[i]),
            min(true_energies_array_hartree[i]),
        )

        # plot the diagonal line
        ax.plot(
            [0, 1],
            [0, 1],
            "k--",
            linewidth=LINEWIDTH,
            alpha=0.5,
            transform=ax.transAxes,
        )

        steps = np.linspace(p2, p1, 5)

        ax.set_xticks(steps)
        ax.set_yticks(steps)
        # convert into str and bold
        steps_str = [rf"$\bf{{{s:.3f}}}$" for s in steps]
        ax.set_xticklabels(steps_str)
        ax.set_yticklabels(steps_str)

        ax.tick_params(
            axis="both",
            which="major",
            labelsize=TICKLABELS_FONTSIZE,
            pad=AXES_PADDING,
            width=LINEWIDTH,
            length=MAJOR_TICK_LENGTH,
            top=False,
            right=False,
        )
        ax.tick_params(
            axis="both",
            which="minor",
            labelsize=TICKLABELS_FONTSIZE,
            pad=AXES_PADDING,
            width=LINEWIDTH,
            length=MINOR_TICK_LENGTH,
            top=False,
            right=False,
        )

        # Show the major grid and style it slightly.
        ax.grid(which="major", color="#DDDDDD", linewidth=LINEWIDTH)
        ax.grid(True)

        ax.set_xlabel(
            "True Energy / Ha",
            fontsize=X_Y_LABELS_FONTSIZE,
            labelpad=LABELPAD,
            fontweight="bold",
        )

        # note that there will be a warning that no axes need legends, that is fine
        # make legend have a frame
        # the fonsize in the legend is for text apart from the title
        # set it to some reasonable value so that the frame is large enough to fit title
        leg = ax.legend(
            facecolor="white",
            framealpha=1,
            frameon=True,
            fontsize=0.01,
            borderpad=LEGEND_BORDERPAD,
            edgecolor="black",
            loc="lower right",
            bbox_to_anchor=(0.85, 0.23),
        )
        # set title as the R^2 value
        leg.set_title(
            rf"$\bf{{R^{2} = {r2_scores[i]:.3f}}}$", prop={"size": X_Y_LABELS_FONTSIZE}
        )
        leg.get_frame().set_linewidth(LEGEND_FRAME_WIDTH)

        max_diff = max(diff[i])

        diff_linspace = np.linspace(0.0, max_diff, 5)

        # colorbar for difference in energies
        cbar = fig.colorbar(scatter_object)
        # if absolute_diff:
        #     cbar.set_label(
        #         "Absolute Difference / kJ mol$^{-1}$", fontsize=54, labelpad=20
        #     )
        # else:
        #     cbar.set_label("Difference / kJ mol$^{-1}$", fontsize=54, labelpad=20)

        cbar.ax.set_yticks(diff_linspace)
        diff_linspace_str = [rf"$\bf{{{s:.2f}}}$" for s in diff_linspace]
        cbar.ax.set_yticklabels(diff_linspace_str)

        cbar.ax.tick_params(
            axis="both", labelsize=TICKLABELS_FONTSIZE, pad=COLORBAR_PADDING
        )

    fig.savefig(filename, pad_inches=PAD_INCHES, dpi=300)
