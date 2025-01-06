from pathlib import Path
from typing import List, Optional, Union
from warnings import warn

import ichor.hpc.global_variables

from ichor.core.common.constants import AIMALL_FUNCTIONALS

from ichor.core.files import PointsDirectory
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_commands import AIMAllCommand
from ichor.hpc.submission_script import SubmissionScript


def submit_points_directory_to_aimall(
    points_directory: Union[PointsDirectory, Path],
    method="B3LYP",
    ncores: int = 2,
    naat: int = 1,
    aimall_atoms: List[str] = None,
    force_calculate_ints=False,
    rerun_on_mogs=False,
    hold: JobID = None,
    script_name: str = ichor.hpc.global_variables.SCRIPT_NAMES["aimall"],
    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"],
    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"],
    **kwargs,
) -> Optional[JobID]:
    """Submits .wfn files which will be partitioned into .int files by
    AIMALL. Each topological atom i the system has its own .int file

    :param points_directory: A path to a `PointsDirectory`-structured directory or a PointsDirectory instance
    :param method: Functional to be written to the .wfn file because AIMAll needs to know it to function correctly.
        Note that only HF, B3LYP, M062X, PBE are supported.
    :param ncores: Number of cores to run AIMAll with, defaults to 2
    :param naat: Number of atoms at a time, defaults to 1
    :param aimall_atoms: A list of atom names (e.g. [C1, H2, etc.]) which to integrate over, defaults to None
        If left as None, AIMAll will do calculations for all atoms.
    :param hold: Hold for a specific JobID, defaults to None
    :raises ValueError: if the provided method is not in the supported functionals, then raise error.
    :return: The job id of the submitted job
    :rtype: Optional[ichor.hpc.batch_system.jobs.JobID]
    """

    if not isinstance(points_directory, PointsDirectory):
        points_directory = PointsDirectory(points_directory)

    method = method.upper().strip()

    # aimall functionals also contains HF, which is the default
    if method not in AIMALL_FUNCTIONALS:
        warn("The functional provided might not be supported by AIMAll.")

    list_of_wfn_paths = add_method_and_get_wfn_paths(points_directory, method)

    ichor.hpc.global_variables.LOGGER.info("Submitting wavefunctions to AIMAll.")
    return submit_wfns(
        list_of_wfn_paths,
        aimall_atoms=aimall_atoms,
        ncores=ncores,
        naat=naat,
        force_calculate_ints=force_calculate_ints,
        rerun_on_mogs=rerun_on_mogs,
        hold=hold,
        script_name=script_name,
        outputs_dir_path=outputs_dir_path,
        errors_dir_path=errors_dir_path,
        **kwargs,
    )


def add_method_and_get_wfn_paths(points: PointsDirectory, method: str) -> List[Path]:
    """AIMALL needs to know the method from the wfn file. The method needs to be
    added in the wfn file, otherwise AIMALL gets the method wrong and
    gives the wrong results."""

    wfns = []
    for point in points:
        # write out the wfn file with the method modified because AIMAll needs to know the functional used
        if point.wfn:
            if point.wfn.exists():
                point.wfn.method = method
                point.wfn.write()
                wfns.append(point.wfn.path)
        else:
            warn(f"Wavefunction file of point {point.path} does not exist.")
            ichor.hpc.global_variables.LOGGER.info(
                f"Wavefunction not found for {point.path}."
            )
    return wfns


def submit_wfns(
    wfns: List[Path],
    aimall_atoms: Optional[List[str]] = None,
    script_name: str = ichor.hpc.global_variables.SCRIPT_NAMES["aimall"],
    ncores=2,
    naat=1,
    force_calculate_ints=False,
    rerun_on_mogs=False,
    hold: Optional[JobID] = None,
    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"],
    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"],
    **kwargs,
) -> Optional[JobID]:
    """Write out submission script and submit wavefunctions to AIMALL on a cluster.

    :param wfns: a list of wavefunction paths which to write to the submission script
    :param atoms: a list of stings corresponding to atom names.
        These will be the atoms for which AIMALL computes properties.
    :param force: Whether or not to compute AIMALL for this wfn. If force is True, AIMALL will be ran again
    :param hold: An optional JobID to hold for. The AIMALL job will not run until that other job is finished.

    """
    with SubmissionScript(
        script_name,
        ncores=ncores,
        outputs_dir_path=outputs_dir_path,
        errors_dir_path=errors_dir_path,
    ) as submission_script:

        nsubmitted_jobs = 0

        for wfn in wfns:
            atomicfiles_dir = (
                wfn.with_suffix("").with_name(f"{wfn.stem}_atomicfiles").exists()
            )

            if force_calculate_ints or not atomicfiles_dir.exists():

                submission_script.add_command(
                    AIMAllCommand(
                        wfn, atoms=aimall_atoms, ncores=ncores, naat=naat, **kwargs
                    )
                )

                nsubmitted_jobs += 1

            elif rerun_on_mogs and any(
                file.suffix == ".mog" for file in atomicfiles_dir.iterdir()
            ):

                submission_script.add_command(
                    AIMAllCommand(
                        wfn, atoms=aimall_atoms, ncores=ncores, naat=naat, **kwargs
                    )
                )

                nsubmitted_jobs += 1

        ichor.hpc.global_variables.LOGGER.info(
            f"Adding {nsubmitted_jobs}/{len(wfns)} to {submission_script.path}. \
                                               {len(wfns)-nsubmitted_jobs} already have INTs calculated."
        )

    # todo this will get executed when running from a compute node,
    # but this does not submit any wfns to aimall, it is just used to make the datafile.
    if len(submission_script.grouped_commands) > 0:
        ichor.hpc.global_variables.LOGGER.info(
            f"Submitting {len(submission_script.grouped_commands)} WFN(s) to AIMAll"
        )
        return submission_script.submit(hold=hold)
    else:
        ichor.hpc.global_variables.LOGGER.info("There are no jobs to submit.")
