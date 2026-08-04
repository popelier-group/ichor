"""Helpers shared by the single geometry optimisation routines (Gaussian, ASE).

A single geometry optimisation is set up in one flat directory per system,
`optimised_geoms/SYSTEM_NAME_program`, which holds the program input, the program
output, and the optimised geometry. No PointsDirectory (and therefore no nested
PointDirectory per geometry) is made, because there is only one geometry involved.
"""

from pathlib import Path
from typing import Optional

import ichor.hpc.global_variables

from ichor.core.atoms import Atoms
from ichor.core.common.io import mkdir
from ichor.core.files import Trajectory


def single_geometry_optimisation_directory(system_name: str, program: str) -> Path:
    """Returns the path of the directory in which a single geometry optimisation
    of the given system is set up and ran.

    :param system_name: Name of the system, i.e. the stem of the input .xyz file
    :param program: Name of the program doing the optimisation, e.g. `gaussian`
    :return: Path of the form `optimised_geoms/SYSTEM_NAME_program`
    """

    return (
        Path(ichor.hpc.global_variables.FILE_STRUCTURE["optimised_geoms"])
        / f"{system_name}_{program}"
    )


def setup_single_geometry_optimisation_directory(
    input_xyz_path: Path, program: str, overwrite_existing: bool
) -> Optional[Path]:
    """Makes the directory in which a single geometry optimisation is set up and ran.

    :param input_xyz_path: Path to the .xyz file containing the geometry to optimise
    :param program: Name of the program doing the optimisation, e.g. `gaussian`
    :param overwrite_existing: Whether to empty the directory if it already exists.
        If it exists and this is False, then None is returned and nothing is written.
    :return: The path of the made directory, or None if the directory already
        exists and is not to be overwritten
    """

    optimisation_dir = single_geometry_optimisation_directory(
        input_xyz_path.stem, program
    )

    if optimisation_dir.exists() and not overwrite_existing:
        print(
            f"ERROR, {optimisation_dir} EXISTS AND OVERWRITE WAS NOT SELECTED. ABORTING"
        )
        return None

    mkdir(optimisation_dir, empty=True)

    return optimisation_dir


def read_single_geometry(input_xyz_path: Path) -> Atoms:
    """Reads the geometry to optimise from the given .xyz file.

    :param input_xyz_path: Path to a .xyz file containing a single geometry. If the
        file contains more than one geometry, the first one is used.
    :return: An `Atoms` instance containing the geometry to optimise
    """

    geometries = Trajectory(input_xyz_path)

    if len(geometries) > 1:
        ichor.hpc.global_variables.LOGGER.warning(
            f"{input_xyz_path} contains {len(geometries)} geometries, "
            "only the first one is going to be optimised."
        )

    return geometries[0]
