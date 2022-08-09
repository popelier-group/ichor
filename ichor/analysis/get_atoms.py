from pathlib import Path

from ichor.atoms import Atoms, AtomsNotFoundError
from ichor.common.io import get_files_of_type
from ichor.files import (
    GJF,
    WFN,
    XYZ,
    OptionalPath,
    PointDirectory,
    PointsDirectory,
    Trajectory,
)


def get_atoms_from_path(path: Path) -> Atoms:
    """
    Returns first instance of `Atoms` found from `path`
    :param path: the `Path` to get atoms from
    :return: the instance of `Atoms` found from path
    :raises: AtomsNotFoundError if no atoms are found
    """
    if path.is_dir():
        if len(get_files_of_type(GJF.filetype, path)) == 0:
            pd = PointsDirectory(path)[0]
        else:
            pd = PointDirectory(path)

        if pd.gjf.exists():
            return pd.gjf.atoms
    elif path.is_file():
        if path.suffix == GJF.filetype:
            return GJF(path).atoms
        elif path.suffix == WFN.filetype:
            return WFN(path).atoms
        elif path.suffix == Trajectory.filetype:
            return XYZ(path).atoms

    raise AtomsNotFoundError(f"Could not find 'Atoms' instance from {path}")


def get_trajectory_from_path(path: Path) -> Trajectory:
    trajectory = Trajectory("")
    if path.is_dir() and PointsDirectory.check_path(path):
        for point in PointsDirectory(path):
            trajectory.append(point.atoms)
    elif Trajectory.check_path(path):
        return Trajectory(path)
    else:
        trajectory.append(get_atoms_from_path(path))
    return trajectory
