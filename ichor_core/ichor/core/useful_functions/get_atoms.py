from pathlib import Path


def get_atoms_from_path(path: Path) -> "ichor.core.atoms.Atoms":  # noqa F821
    """
    Returns first instance of `Atoms` found from `path`
    :param path: the `Path` to get atoms from
    :return: the instance of `Atoms` found from path
    :raises: AtomsNotFoundError if no atoms are found
    """
    from ichor.core.atoms import AtomsNotFoundError
    from ichor.core.common.io import get_files_of_type
    from ichor.core.files import (
        GJF,
        PointDirectory,
        PointsDirectory,
        Trajectory,
        WFN,
        XYZ,
    )

    if path.is_dir():
        if len(get_files_of_type(GJF.get_filetype(), path)) == 0:
            pd = PointsDirectory(path)[0]
        else:
            pd = PointDirectory(path)

        if pd.gjf:
            if pd.gjf.exists():
                return pd.gjf.atoms

    elif path.is_file():
        if GJF.check_path(path):
            return GJF(path).atoms
        elif WFN.check_path(path):
            return WFN(path).atoms
        elif Trajectory.check_path(path):
            return XYZ(path).atoms

    raise AtomsNotFoundError(f"Could not find 'Atoms' instance from {path}")


def get_trajectory_from_path(
    path: Path, trajectory_name: str = "new_trajectory.xyz"
) -> "ichor.core.files.Trajectory":  # noqa F821

    from ichor.core.files import PointsDirectory, Trajectory

    trajectory = Trajectory(trajectory_name)
    if path.is_dir() and PointsDirectory.check_path(path):
        for point in PointsDirectory(path):
            trajectory.append(point.atoms)
    elif Trajectory.check_path(path):
        return Trajectory(path)
    else:
        trajectory.append(get_atoms_from_path(path))
    return trajectory
