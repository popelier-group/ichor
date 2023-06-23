import math
import warnings

from string import ascii_uppercase
from typing import List, Union

import matplotlib

import numpy as np
from ichor.core.files.dl_poly import DlPolyFFLUX, FFLUXDirectory
from matplotlib import pyplot as plt

ascii_uppercase = list(ascii_uppercase)

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

except ImportError:
    warnings.warn("Could not import scienceplots. Will not use scienceplots styles.")


def round_base_10(x):
    if x < 0:
        return 0
    elif x == 0:
        return 10
    return math.ceil(math.log10(x))


def format_energy_plots(
    ax,
    xlabel="Timestep",
    major_grid_linewidth=4.0,
    minor_grid_linewidth=4.0,
    xlabel_fontsize=20,
    label_pad=1.0,
    tick_params_labelsize=48,
    tick_params_pad=15,
    major_tick_params_length=6.0,
    major_tick_params_width=4,
    minor_tick_params_length=3.0,
    minor_tick_params_width=4.0,
):

    # Show the major grid and style it slightly.
    ax.grid(which="major", color="#DDDDDD", linewidth=major_grid_linewidth)
    # Show the minor grid as well. Style it in very light gray as a thin,
    # dotted line.
    # ax.grid(which="minor", color="#EEEEEE", linestyle=":", linewidth=minor_grid_linewidth)
    # Make the minor ticks and gridlines show.
    # ax.minorticks_on()
    # ax.grid(True)

    ax.set_xlabel(
        xlabel, fontsize=xlabel_fontsize, labelpad=label_pad, fontweight="bold"
    )

    ax.tick_params(
        axis="both",
        which="major",
        labelsize=tick_params_labelsize,
        pad=tick_params_pad,
        length=major_tick_params_length,
        width=major_tick_params_width,
        top=False,
        right=False,
    )
    ax.tick_params(
        axis="both",
        which="minor",
        labelsize=tick_params_labelsize,
        pad=tick_params_pad,
        length=minor_tick_params_length,
        width=minor_tick_params_width,
        top=False,
        right=False,
    )

    tick_labels = ax.get_xticklabels() + ax.get_yticklabels()
    for t in tick_labels:
        t.set_fontweight("bold")


def plot_total_energy(
    data: Union[DlPolyFFLUX, FFLUXDirectory, List[DlPolyFFLUX], List[FFLUXDirectory]],
    until_converged: bool = True,
    reference: List[float] = None,
    FIGURE_LABEL_SIZE=30,
    X_Y_LABELS_FONTSIZE=30,
    TICKLABELS_FONTSIZE=22,
    LABELPAD=10,
    AXES_PADDING=10.0,
    LINEWIDTH=2.0,
    MAJOR_TICK_LENGTH=6.0,
    MINOR_TICK_LENGTH=3.0,
    PAD_INCHES=0.05,
    filename: str = "total_energy.svg",
):

    """Plots the predicted total energy of the system (in kJ mol-1) from the fflux
    simulation for every timestep.

    If until_coverged is True, it will only plot the timesteps until the timestep
    where the difference to the next timestep is less that 1e-4 kJ mol-1.

    :param data: A FFLUX file or directory containing a FFLUX file to read data from.
    :param until_converged: Plot timesteps until energy is converted to 1e-4 kJ mol-1, defaults to True.
    :param reference: A reference value to subtract (could be the Gaussian optimized minimum).
        This value has to be in kJ mol-1. If a list is passed in as data, then this reference must also be a
        list of the same length as data.
    :param FIGURE_LABEL_SIZE: The size of the figure labels (A, B, C, etc.), defaults to 30
    :param X_Y_LABELS_FONTSIZE: The size of the x and y axis labels, defaults to 30
    :param TICKLABELS_FONTSIZE: The size of the tick labels on the axes, defaults to 22
    :param LABELPAD: The padding of the x and y labels from the plot, defaults to 10
    :param AXES_PADDING: The padding of the number on the axes from the plots, defaults to 10.0
    :param LINEWIDTH: The width of the lines, defaults to 2.0
    :param MAJOR_TICK_LENGTH: The length of the major ticks, defaults to 6.0
    :param MINOR_TICK_LENGTH: The length of the minor ticks, defaults to 3.0
    :param PAD_INCHES: Padding on the sides of the plot (as tight layout is used), defaults to 0.05
    :param filename: The filename to save as. Note that the extension determines how the fine is saved (png, svg),
         defaults to "total_energy.svg"
    """

    # get data from somewhere
    if not isinstance(data, list):
        fflux_files = [data]
    if isinstance(data[0], DlPolyFFLUX):
        fflux_files = data
    elif isinstance(data[0], FFLUXDirectory):
        fflux_files = [d.fflux_file for d in data]

    nplots = len(fflux_files)
    WIDTH = 12 * nplots
    HEIGHT = WIDTH / 4

    fig, axes = plt.subplots(1, nplots, figsize=(WIDTH, HEIGHT), sharey=True)

    idx_where_energy_diff_less_than = [
        f.first_index_where_delta_less_than() for f in fflux_files
    ]
    total_eng_kj_mol = [f.total_energy_kj_mol for f in fflux_files]

    if reference:
        total_eng_kj_mol = [tot - ref for tot, ref in zip(total_eng_kj_mol, reference)]
        with open("difference_between_reference_and_fflux.txt", "w") as writef:
            for i, t in enumerate(total_eng_kj_mol):
                diff_ref_and_fflux = t[idx_where_energy_diff_less_than[i]]
                writef.write(
                    f"Difference kJ mol-1 for fflux file {fflux_files[i]}: {diff_ref_and_fflux}"
                )

    if not isinstance(axes, np.ndarray):
        axes = [axes]

    if until_converged:

        total_eng_kj_mol = [
            t[:i] for i, t in zip(idx_where_energy_diff_less_than, total_eng_kj_mol)
        ]

        for i, ax in enumerate(axes):
            current_idx = idx_where_energy_diff_less_than[i]
            current_total_eng = total_eng_kj_mol[i]

            ax.text(
                0.9,
                0.88,
                f"{ascii_uppercase[i]}",
                fontsize=FIGURE_LABEL_SIZE,
                transform=ax.transAxes,
                fontweight="bold",
            )

            ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(4))
            ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(4))

            ax.plot(range(current_idx), current_total_eng, linewidth=LINEWIDTH)

    else:

        for i, ax in enumerate(axes):
            current_total_eng = total_eng_kj_mol[i]
            current_fflux_file = fflux_files[i]

            ax.text(
                0.1,
                0.85,
                rf"$\bf{{{ascii_uppercase[i]}}}$",
                fontsize=FIGURE_LABEL_SIZE,
                transform=ax.transAxes,
            )

            ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(4))
            ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator(4))

            ax.plot(
                range(current_fflux_file.ntimesteps),
                current_total_eng,
                linewidth=LINEWIDTH,
            )

    for ax in axes:

        format_energy_plots(
            ax,
            xlabel="Timestep",
            major_grid_linewidth=LINEWIDTH,
            minor_grid_linewidth=LINEWIDTH,
            xlabel_fontsize=X_Y_LABELS_FONTSIZE,
            label_pad=LABELPAD,
            tick_params_labelsize=TICKLABELS_FONTSIZE,
            tick_params_pad=AXES_PADDING,
            major_tick_params_length=MAJOR_TICK_LENGTH,
            major_tick_params_width=LINEWIDTH,
            minor_tick_params_length=MINOR_TICK_LENGTH,
            minor_tick_params_width=LINEWIDTH,
        )

    # only set the y label for first plot
    axes[0].set_ylabel(
        ylabel="Energy / kJ mol$^{-1}$",
        fontsize=X_Y_LABELS_FONTSIZE,
        labelpad=LABELPAD,
        fontweight="bold",
    )

    fig.savefig(filename, pad_inches=PAD_INCHES, dpi=300)


def plot_total_energy_from_array(
    data: np.ndarray,
    title: str = "",
    reference: float = None,
):
    """Plots the given predicted data (in kJ mol-1) against timesteps

    If until_coverged is True, it will only plot the timesteps until the timestep
    where the difference to the next timestep is less that 1e-4 kJ mol-1.

    :param data: A np array containing predicted total energy data
    :param title: Title for plot
    :param referece: reference Gaussain energy
    """

    fig, ax = plt.subplots(figsize=(9, 9))

    total_eng = data

    ax.plot(range(len(total_eng)), total_eng)

    if reference:
        ax.plot(range(len(total_eng)), [reference] * len(total_eng))

    ax.set_xlabel("Timestep", fontsize=24)
    ax.set_ylabel("Energy / kJ mol$^{-1}$", fontsize=24)

    format_energy_plots(ax, title)

    plt.show()


def plot_differences(
    data: Union[DlPolyFFLUX, FFLUXDirectory],
    until_converged: bool = True,
    absolute: bool = False,
    title: str = "",
):
    """Plots the differences between one timestep and the next timestep (in kJ mol-1) from the FFLUX
    file for every pair of timesteps

    If until_coverged is True, it will only plot the difference until the timestep
    where the difference to the next timestep is less that 1e-4 kJ mol-1.

    :param data: A FFLUX file or directory containing a FFLUX file to read data from.
    :param until_converged: Plot timesteps and ifference until energy is converted to 1e-4 kJ mol-1, defaults to True
    :param absolute: Plot the absolute of the differences between each timestep
    :param title: Title for plot
    """

    # get data from somewhere
    if isinstance(data, DlPolyFFLUX):
        fflux_file = data
    elif isinstance(data, FFLUXDirectory):
        fflux_file = data.fflux_file

    fig, ax = plt.subplots(figsize=(9, 9))

    idx = fflux_file.first_index_where_delta_less_than()

    if absolute:
        deltas = np.abs(fflux_file.delta_between_timesteps_kj_mol)
    else:
        deltas = fflux_file.delta_between_timesteps_kj_mol

    if until_converged:
        final_energy = deltas[idx]
        ax.plot(range(idx), deltas[:idx] - final_energy)
    else:
        ax.plot(range(fflux_file.ntimesteps), deltas)

    ax.set_xlabel("Timestep", fontsize=24)
    if absolute:
        ax.set_ylabel("Absolute Energy / kJ mol$^{-1}$", fontsize=24)
    else:
        ax.set_ylabel("Energy / kJ mol$^{-1}$", fontsize=24)

    format_energy_plots(ax, title)

    plt.show()
