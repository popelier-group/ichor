import warnings
from typing import Union

import numpy as np
from ichor.core.files.dl_poly import DlPolyFFLUX, FFLUXDirectory
from matplotlib import pyplot as plt

try:
    import scienceplots  # noqa

    plt.style.use("science")
except ImportError:
    warnings.warn("Could not import scienceplots. Will not use scienceplots styles.")


def format_energy_plots(ax, title: str = ""):

    # Show the major grid and style it slightly.
    ax.grid(which="major", color="#DDDDDD", linewidth=1.2)
    ax.grid(True)

    if title:
        ax.set_title(title, fontsize=28)

    ax.tick_params(axis="both", which="major", labelsize=18)


def plot_total_energy(
    data: Union[DlPolyFFLUX, FFLUXDirectory],
    until_converged: bool = True,
    reference: float = None,
    title: str = "",
):
    """Plots the predicted total energy of the system (in kJ mol-1) from the fflux
    simulation for every timestep.

    If until_coverged is True, it will only plot the timesteps until the timestep
    where the difference to the next timestep is less that 1e-4 kJ mol-1.

    :param data: A FFLUX file or directory containing a FFLUX file to read data from.
    :param until_converged: Plot timesteps until energy is converted to 1e-4 kJ mol-1, defaults to True.
    :param reference: A reference value to subtract (could be the Gaussian optimized minimum)
    :param title: Title for plot
    """

    # get data from somewhere
    if isinstance(data, DlPolyFFLUX):
        fflux_file = data
    elif isinstance(data, FFLUXDirectory):
        fflux_file = data.fflux_file

    fig, ax = plt.subplots(figsize=(9, 9))

    idx = fflux_file.first_index_where_delta_less_than()
    total_eng = fflux_file.total_energy_kj_mol

    if reference:
        total_eng = total_eng - reference

    if until_converged:
        ax.plot(range(idx), total_eng[:idx])
    else:
        ax.plot(range(fflux_file.ntimesteps), total_eng)

    ax.set_xlabel("Timestep", fontsize=24)
    ax.set_ylabel("Energy / kJ mol$^{-1}$", fontsize=24)

    format_energy_plots(ax, title)

    plt.show()


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
