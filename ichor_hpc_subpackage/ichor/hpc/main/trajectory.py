from pathlib import Path

from ichor.core.atoms import ALF
from ichor.hpc.global_variables import SCRIPT_NAMES
from ichor.hpc.useful_functions.submit_free_flow_python_on_compute import (
    submit_free_flow_python_command_on_compute,
)


def submit_center_trajectory_on_atom(
    trajectory_path: Path,
    central_atom_name,
    central_atom_alf: ALF,
    xyz_output_path="ALF_centered_trajectory.xyz",
    ncores=1,
):

    # only need central atom alf as we are centering on it
    alf_dict = {central_atom_name, central_atom_alf}

    text_list = []
    # make the python command that will be written in the submit script
    # it will get executed as `python -c python_code_to_execute...`
    text_list.append("from ichor.core.files import Trajectory")
    text_list.append("from ichor.core.atoms import ALF")
    text_list.append(f"traj = Trajectory('{trajectory_path}')")
    text_list.append(
        f"traj.center_geometries_on_atom_and_write_xyz('{central_atom_name}', {alf_dict}, '{xyz_output_path}')"
    )

    return submit_free_flow_python_command_on_compute(
        text_list, SCRIPT_NAMES["center_trajectory"], ncores=ncores
    )
