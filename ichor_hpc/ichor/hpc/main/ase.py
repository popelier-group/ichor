import shutil
from pathlib import Path
from typing import List, Optional, Union

import ichor.hpc.global_variables
from ichor.core.common.io import mkdir

from ichor.core.files import PointsDirectory, Trajectory, XTB
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_commands import PythonCommand
from ichor.hpc.submission_script import SubmissionScript


def submit_single_ase_xyz(
    input_xyz_path: Union[str, Path],
    ncores=2,
    method="GFN2-xT",
    solvent="none",
    electronic_temperature=300,
    max_iterations=2048,
    fmax=0.01,
    overwrite=False,
    hold: JobID = None,
    **kwargs,
) -> Optional[JobID]:

    input_xyz_traj = Trajectory(input_xyz_path)
    opt_dir = Path(ichor.hpc.global_variables.FILE_STRUCTURE["optimised_geoms"])
    mkdir(opt_dir)
    system_name = input_xyz_path.stem
    traj_dir = input_xyz_traj.to_dir(system_name, every=1, center=False)
    opt_path = Path(opt_dir / traj_dir.name)

    try:
        shutil.move(traj_dir, opt_dir)
    except FileExistsError:
        if overwrite:
            try:
                rm_path = opt_path
                shutil.rmtree(rm_path)
                shutil.move(traj_dir, opt_dir)
            except FileNotFoundError:
                print("FILE DOES NOT EXIST FOR OVERWRITE. RUNNING AS NORMAL")
                pass
        else:
            shutil.rmtree(traj_dir)
            print("ERROR, FILE EXISTS AND OVERWRITE WAS NOT SELECTED. ABORTING")
            return

    opt_path = Path(opt_dir / traj_dir.name)

    submit_points_directory_to_ase(
        points_directory=opt_path,
        input_xyz_path=input_xyz_path,
        ncores=ncores,
        method=method,
        solvent=solvent,
        electronic_temperature=electronic_temperature,
        max_iterations=max_iterations,
        fmax=fmax,
        hold=hold,
        outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"]
        / input_xyz_path.name
        / "ASE",
        errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"]
        / input_xyz_path.name
        / "ASE",
    )


def submit_points_directory_to_ase(
    points_directory: Union[Path, PointsDirectory],
    ncores=2,
    hold: JobID = None,
    script_name: str = ichor.hpc.global_variables.SCRIPT_NAMES["xtb"],
    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"],
    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"],
    **kwargs,
) -> Optional[JobID]:
    """Function that writes out XTB input files from .xyz files that are in each directory and
    calls submit_gjfs which submits all .xyz files in a directory to ASE.

    :param directory: A Path object which is the path of the directory
        (commonly traning set path, sample pool path, etc.).
    :param kwargs: Key word arguments to pass to GJF class. These are things like number of cores, basis set,
        level of theory, spin multiplicity, charge, etc.
        These will get used in the new written gjf files (overwriting
        settings from previously existing gjf files)
    """
    # a directory which contains points (a bunch of molecular geometries)
    if not isinstance(points_directory, PointsDirectory):
        points_directory = PointsDirectory(points_directory)

    xtb_files = write_xtb_input(points_directory, **kwargs)
    return submit_xtb(
        xtb_files,
        script_name=script_name,
        ncores=ncores,
        hold=hold,
        outputs_dir_path=outputs_dir_path,
        errors_dir_path=errors_dir_path,
    )


def write_xtb_input(points_directory: PointsDirectory, **kwargs) -> List[Path]:
    """Writes out .py files in every PointDirectory which is contained
    in a PointsDirectory. Each PointDirectory should always have a `.xyz` file in it,
    which contains only one molecular geometry. This `.xyz` file can be used to write out the `.py`
    file in the PointDirectory (if it does not exist already).

    :param points: A PointsDirectory instance which wraps around a
        whole directory containing points (such as TRAINING_SET).
    :return: A list of Path objects which point to `.py` files in each
        PointDirectory that is contained in the PointsDirectory.
    """

    xtbs = []

    for point_directory in points_directory:

        # remove the .pointdirectory suffix
        xtb_file_name = (
            point_directory.path.with_suffix("").name + "_opt" + XTB.get_filetype()
        )

        xyz_file_name = point_directory.path.with_suffix("").name + ".xyz"
        # set to run xtb calc in opt geometry folder
        xtb_xyz = Path(point_directory.path / xyz_file_name)

        # write instance of xtb class
        point_directory.xtb = XTB(
            Path(point_directory.path / xtb_file_name),
            input_xtb_path=xtb_xyz,
            output_xyz_path=str(xtb_xyz).replace(".xyz", "_optimised.xyz"),
            traj_path=str(xtb_xyz).replace(".xyz", ".traj"),
            log_path=str(xtb_xyz).replace(".xyz", ".log"),
            **kwargs,
        )
        point_directory.xtb.write()

        xtbs.append(point_directory.xtb.path)

    return xtbs


def submit_xtb(
    xtbs: List[Path],
    script_name: Optional[Union[str, Path]] = ichor.hpc.global_variables.SCRIPT_NAMES[
        "xtb"
    ],
    hold: Optional[JobID] = None,
    ncores=2,
    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"],
    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"],
) -> JobID:
    """Function that writes out a submission script which contains an array of
    Gaussian jobs to be ran on compute nodes. If calling this function from
    a log-in node, it will write out the submission script, a datafile (file which contains the names of
    all the .gjf file that need to be ran through Gaussian),
    and it will submit the submission script to compute nodes as well to run Gaussian on compute nodes.
    However, if using this function from a compute node,
    (which will happen when ichor is ran in auto-run mode), this function will only be used to write out
    the datafile and will not submit any new jobs
    from the compute node (as you cannot submit jobs from compute nodes on CSF3.)

    :param gjfs: A list of Path objects pointing to .gjf files
    :param force_calculate_wfn: Run Gaussian calculations on given .gjf files,
        even if .wfn files already exist. Defaults to False.
    :script_name: Path to write submission script out to defaults to ichor.hpc.global_variables.SCRIPT_NAMES["gaussian"]
    :param hold: An optional JobID for which this job to hold.
        This is used in auto-run to hold this job for the previous job to finish, defaults to None
    :return: The JobID of this job given by the submission system.
    """

    # make a SubmissionScript instance which is going to contain all the jobs that are going to be ran
    # the submission_script object can be accessed even after the context manager
    with SubmissionScript(
        script_name,
        ncores=ncores,
        outputs_dir_path=outputs_dir_path,
        errors_dir_path=errors_dir_path,
    ) as submission_script:

        number_of_jobs = 0

        for xtb in xtbs:
            submission_script.add_command(PythonCommand(xtb))
            number_of_jobs += 1

        ichor.hpc.global_variables.LOGGER.info(
            f"Added {number_of_jobs} / {len(xtbs)} ASE optimisation jobs to {submission_script.path}"
        )

    # submit on compute node if there are files to submit
    if len(submission_script.grouped_commands) > 0:
        ichor.hpc.global_variables.LOGGER.info(
            f"Submitting {len(submission_script.grouped_commands)} optimisation(s) to ASE"
        )
        return submission_script.submit(hold=hold)
    else:
        raise ValueError("There are no jobs to submit in the submission script.")
