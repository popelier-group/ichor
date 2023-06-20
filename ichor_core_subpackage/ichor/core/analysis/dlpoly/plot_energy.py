import warnings
from typing import List, Union

import numpy as np
from ichor.core.files.dl_poly import DlPolyFFLUX, FFLUXDirectory
from matplotlib import pyplot as plt

try:
    import scienceplots  # noqa

    plt.style.use("science")
except ImportError:
    warnings.warn("Could not import scienceplots. Will not use scienceplots styles.")


def format_energy_plots(ax, xlabel="Timestep", fontsize=54, labelpad=20):

    # Show the major grid and style it slightly.
    ax.grid(which="major", color="#DDDDDD", linewidth=4.0)
    # Show the minor grid as well. Style it in very light gray as a thin,
    # dotted line.
    ax.grid(which="minor", color="#EEEEEE", linestyle=":", linewidth=4)
    # Make the minor ticks and gridlines show.
    ax.minorticks_on()
    ax.grid(True)

    ax.set_xlabel(xlabel, fontsize=fontsize, labelpad=labelpad)

    # ax.tick_params(axis="both", which="major", labelsize=48, length=3, width=2, pad=15)
    # ax.tick_params(axis="both", which="minor", labelsize=48, length=3, width=2, pad=15)

    ax.tick_params(axis="both", which="major", labelsize=48, pad=15)
    ax.tick_params(axis="both", which="minor", labelsize=48, pad=15)


def plot_total_energy(
    data: Union[DlPolyFFLUX, FFLUXDirectory, List[DlPolyFFLUX], List[FFLUXDirectory]],
    until_converged: bool = True,
    reference: float = None,
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
    """

    # get data from somewhere
    if not isinstance(data, list):
        fflux_files = [data]

    if isinstance(data[0], DlPolyFFLUX):
        fflux_files = data
    elif isinstance(data[0], FFLUXDirectory):
        fflux_files = [d.fflux_file for d in data]

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

    nplots = len(fflux_files)
    fig, axes = plt.subplots(1, nplots, figsize=(15 * nplots, 10), sharey=True)

    if not isinstance(axes, np.ndarray):
        axes = [axes]

    if until_converged:

        total_eng_kj_mol = [
            t[:i] for i, t in zip(idx_where_energy_diff_less_than, total_eng_kj_mol)
        ]

        for i, ax in enumerate(axes):
            current_idx = idx_where_energy_diff_less_than[i]
            current_total_eng = total_eng_kj_mol[i]

            ax.plot(range(current_idx), current_total_eng, linewidth=2)

    else:

        for i, ax in enumerate(axes):
            current_total_eng = total_eng_kj_mol[i]
            current_fflux_file = fflux_files[i]

            ax.plot(
                range(current_fflux_file.ntimesteps), current_total_eng, linewidth=2
            )

    for ax in axes:
        format_energy_plots(ax, xlabel="Timestep", fontsize=54, labelpad=20)
    # only set the y label for first plot
    axes[0].set_ylabel(ylabel="Energy / kJ mol$^{-1}$", fontsize=54, labelpad=20)

    plt.savefig(filename, pad_inches=0.2)


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
