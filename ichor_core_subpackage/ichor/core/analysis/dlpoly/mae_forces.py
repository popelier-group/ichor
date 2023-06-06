import warnings

import numpy as np
from ichor.core.common.constants import bohr2ang
from matplotlib import pyplot as plt

try:
    import scienceplots  # noqa

    plt.style.use("science")
except ImportError:
    warnings.warn("Could not import scienceplots. Will not use scienceplots styles.")


def mae_forces(predicted_forces_array: np.ndarray, true_forces_array: np.ndarray):
    """Plots a matshow in matplotlib of the MAE of the predicted forces array vs
    the true forces array

    :param predicted_forces_array: Predicted forces array of shape ntimesteps x natoms x 3.
    :param true_forces_array:  True forces array of shape ntimesteps x natoms x 3
    """

    diff = np.abs(predicted_forces_array - true_forces_array)
    mae_diff = np.sum(diff, axis=0) / diff.shape[0]

    # convert to kcal mol-1 ang-1
    conversion_factor = 627.5 / bohr2ang

    mae_diff_kcal_mol_ang = mae_diff * conversion_factor

    fig, ax = plt.subplots(figsize=(9, 9))
    ax_object = ax.matshow(mae_diff_kcal_mol_ang)
    cbar = fig.colorbar(ax_object)

    ax.set_xticks(range(3))
    ax.set_xticklabels(["x", "y", "z"], fontsize=18)
    ax.set_yticks(range(4))
    ax.set_yticklabels(["N1", "H2", "H3", "H4"], fontsize=18)

    for (i, j), z in np.ndenumerate(mae_diff_kcal_mol_ang):
        ax.text(
            j,
            i,
            "{:0.3f}".format(z),
            ha="center",
            va="center",
            bbox=dict(boxstyle="round", facecolor="white", edgecolor="black"),
        )

    # colorbar for difference in energies
    cbar.set_label("Mean Absolute Error / kcal mol$^{-1}$ Å$^{-1}$", fontsize=24)

    ax.tick_params(axis="both", which="both", length=0)

    plt.show()
