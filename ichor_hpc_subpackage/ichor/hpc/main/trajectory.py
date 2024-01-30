from pathlib import Path
from typing import Dict

from ichor.core.atoms import ALF
from ichor.hpc.global_variables import SCRIPT_NAMES
from ichor.hpc.useful_functions.submit_free_flow_python_on_compute import (
    submit_free_flow_python_command_on_compute,
)


def submit_center_trajectory_on_atom(
    trajectory_path: Path,
    central_atom_name: str,
    alf_dict: Dict[str, ALF],
    xyz_output_path="ALF_centered_trajectory.xyz",
    ncores=1,
):
    """Submits centering on atom on compute

    :param trajectory_path: Path of trajectory file to center
    :param central_atom_name: Central atom name to center on, eg. C1
    :param alf_dict: dictionary of atom_name: ALF, which must contain the central atom as key
    :param xyz_output_path: xyz file to write centered geometries to, defaults to "ALF_centered_trajectory.xyz"
    :param ncores: number of cores for job, defaults to 1
    """

    text_list = []
    # make the python command that will be written in the submit script
    # it will get executed as `python -c python_code_to_execute...`
    text_list.append("from ichor.core.files import Trajectory")
    text_list.append("from ichor.core.atoms import ALF")
    text_list.append(f"traj = Trajectory('{str(trajectory_path.absolute())}')")
    text_list.append(
        f"traj.center_geometries_on_atom_and_write_xyz('{central_atom_name}', {alf_dict}, '{xyz_output_path}')"
    )

    return submit_free_flow_python_command_on_compute(
        text_list, SCRIPT_NAMES["center_trajectory"], ncores=ncores
    )
