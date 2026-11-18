from pathlib import Path
from typing import List, Optional, Union
from warnings import warn

import ichor.hpc.global_variables

from ichor.core.common.constants import AIMALL_FUNCTIONALS

from ichor.core.files import PointDirectory, PointsDirectory
from ichor.core.files.gaussian import WFX
from ichor.core.processing.points_directory_check import wfx_is_finished
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_commands import AIMAllCommand
from ichor.hpc.submission_script import SubmissionScript
from tqdm import tqdm


def submit_points_directory_to_aimall(
    points_directory: Union[PointsDirectory, Path, List[PointDirectory]],
    method="B3LYP",
    ncores: int = 2,
    naat: int = 1,
    aimall_atoms: List[str] = None,
    force_calculate_ints=False,
    hold: JobID = None,
    script_name: str = ichor.hpc.global_variables.SCRIPT_NAMES["aimall"],
    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"],
    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"],
    **kwargs,
) -> Optional[JobID]:
    """Submits .wfx files which will be partitioned into .int files by
    AIMALL. Each topological atom i the system has its own .int file

    :param points_directory: A path to a `PointsDirectory`-structured directory, a
        PointsDirectory instance, or a list of the PointDirectory-ies of interest. The
        last of these is used to submit only some of the points of a PointsDirectory,
        such as the ones which have to be calculated again.
    :param method: Fallback functional when the WFX has no Model and the GJF has no method.
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

    # a PointsDirectory or a list of PointDirectory-ies is already the points to submit
    if isinstance(points_directory, (str, Path)):
        points_directory = PointsDirectory(points_directory)

    method = method.upper().strip()

    # aimall functionals also contains HF, which is the default
    if method not in AIMALL_FUNCTIONALS:
        warn("The functional provided might not be supported by AIMAll.")

    list_of_wfx_paths = add_method_and_get_wfx_paths(points_directory, method)

    ichor.hpc.global_variables.LOGGER.info("Submitting wavefunctions to AIMAll.")
    return submit_wfxs(
        list_of_wfx_paths,
        aimall_atoms=aimall_atoms,
        ncores=ncores,
        naat=naat,
        force_calculate_ints=force_calculate_ints,
        hold=hold,
        script_name=script_name,
        outputs_dir_path=outputs_dir_path,
        errors_dir_path=errors_dir_path,
        **kwargs,
    )


def add_method_and_get_wfx_paths(
    points: Union[PointsDirectory, List[PointDirectory]], method: str
) -> List[Path]:
    """Collect WFX inputs and fill in missing AIMAll Model sections.

    :param points: A PointsDirectory instance, or a list of the PointDirectory-ies whose
        wavefunctions are to be written out with the method in them.
    :param method: The method (functional) used in the Gaussian calculation.
    """

    wfxs = []
    for point in tqdm(points, desc="Extracting WFX files"):
        wfx = point.wfx
        if isinstance(wfx, list):
            warn(f"Multiple WFX files found for {point.path}. Point skipped.")
            continue
        if not wfx or not wfx.exists():
            warn(f"WFX file of point {point.path} does not exist.")
            continue
        try:
            if not wfx.method:
                gjf = point.gjf
                gjf_method = gjf.method if gjf and not isinstance(gjf, list) else None
                wfx.ensure_model(gjf_method or method)
        except (OSError, ValueError, StopIteration) as exc:
            warn(f"Could not prepare {wfx.path} for AIMAll: {exc}")
            continue
        wfxs.append(wfx.path)
    return wfxs


def submit_wfxs(
    wfxs: List[Path],
    aimall_atoms: Optional[List[str]] = None,
    script_name: str = ichor.hpc.global_variables.SCRIPT_NAMES["aimall"],
    ncores=2,
    naat=1,
    force_calculate_ints=False,
    hold: Optional[JobID] = None,
    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"],
    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"],
    **kwargs,
) -> Optional[JobID]:
    """Write out submission script and submit wavefunctions to AIMALL on a cluster.

    :param wfxs: a list of wavefunction paths which to write to the submission script
    :param atoms: a list of stings corresponding to atom names.
        These will be the atoms for which AIMALL computes properties.
    :param force: Whether or not to compute AIMALL for this wfx. If force is True, AIMALL will be ran again
    :param hold: An optional JobID to hold for. The AIMALL job will not run until that other job is finished.

    """
    with SubmissionScript(
        script_name,
        ncores=ncores,
        outputs_dir_path=outputs_dir_path,
        errors_dir_path=errors_dir_path,
    ) as submission_script:

        nsubmitted_jobs = 0

        for wfx in tqdm(wfxs, desc="Submitting WFX files"):

            wfx = Path(wfx)
            if not WFX.check_path(wfx) or not wfx_is_finished(wfx):
                warn(f"AIMAll requires a complete WFX file. Skipping {wfx}.")
                continue
            atomic_files = wfx.with_name(f"{wfx.stem}_atomicfiles")
            aim_output = wfx.with_suffix(".aim")
            if (
                force_calculate_ints
                or not atomic_files.is_dir()
                or not aim_output.is_file()
                or aim_output.stat().st_mtime_ns < wfx.stat().st_mtime_ns
            ):

                submission_script.add_command(
                    AIMAllCommand(
                        wfx, atoms=aimall_atoms, ncores=ncores, naat=naat, **kwargs
                    )
                )

                nsubmitted_jobs += 1

        ichor.hpc.global_variables.LOGGER.info(
            f"Adding {nsubmitted_jobs}/{len(wfxs)} to {submission_script.path}. \
                                               {len(wfxs) - nsubmitted_jobs} already have INTs calculated."
        )

    # todo this will get executed when running from a compute node,
    # but this does not submit any wfxs to aimall, it is just used to make the datafile.
    if len(submission_script.grouped_commands) > 0:
        ichor.hpc.global_variables.LOGGER.info(
            f"Submitting {len(submission_script.grouped_commands)} WFX(s) to AIMAll"
        )
        return submission_script.submit(hold=hold)
    else:
        ichor.hpc.global_variables.LOGGER.info("There are no jobs to submit.")
