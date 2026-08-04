import math
import re
from pathlib import Path
from typing import Optional, Union

import ichor.hpc.global_variables
import numpy as np

from ichor.core.common.io import mkdir
from ichor.core.files import Trajectory
from ichor.core.files.dl_poly import (
    DlPolyConfig,
    DlPolyControl,
    DlPolyFFLUXInput,
    DlPolyField,
    DlPolyMpoles,
)
from ichor.core.models import Models
from ichor.hpc.batch_system.jobs import JobID
from ichor.hpc.submission_commands import DlpolyCommand
from ichor.hpc.submission_script import SubmissionScript
from ichor.hpc.useful_functions.submit_free_flow_python_on_compute import (
    submit_free_flow_python_command_on_compute,
)
from tqdm import tqdm


def _copy_model_with_clean_system_name(
    src_path: Path,
    dst_path: Path,
    system_name: str,
    clean_system_name: str,
) -> None:
    """Copy a FEREBUS ``.model`` file, rewriting the system name on its ``[system]``
    ``name`` line to an underscore-free version.

    The FFLUX model reader (``fflux_read_models.f90``) reconstructs the model *file name*
    it opens for the data read from the ``SystemName`` it parses out of this ``name`` line,
    so the value has to agree with the (underscore-free) copied file name and the CONFIG
    atom labels. Everything else in the file (dimensions, ALF, kernels, weights, training
    data) is copied verbatim.

    :param src_path: The original ``.model`` file to copy.
    :param dst_path: The destination path (already carrying the underscore-free name).
    :param system_name: The original system name (with underscores) as it appears on the
        model file's ``name`` line.
    :param clean_system_name: The underscore-free system name to write in its place.
    """
    lines = src_path.read_text().splitlines(keepends=True)
    for idx, line in enumerate(lines):
        stripped = line.strip()
        # the "[system]" section's name line, e.g. "name BZAMID05_MOL_MTD_OUT0"
        if (
            stripped.startswith("name ")
            and stripped[len("name ") :].strip() == system_name
        ):
            prefix = line[: len(line) - len(line.lstrip())]
            suffix = "\n" if line.endswith("\n") else ""
            lines[idx] = f"{prefix}name {clean_system_name}{suffix}"
            break
    dst_path.write_text("".join(lines))


def write_dlpoly_fflux_setup(
    run_path: Union[str, Path],
    model_directory: Union[str, Path],
    starting_geometry: Union[str, Path],
    ensemble: str = "nvt",
    temperature: int = 1,
    timestep: float = 0.001,
    nsteps: int = 500,
    electrostatics: str = "ewald",
    electrostatics_level: Optional[int] = None,
    cell_size: float = 50.0,
    cutoff: Optional[float] = None,
    cap: Optional[float] = None,
    progress_bar: bool = True,
) -> Path:
    """Sets up a directory from which a DL_FFLUX (FFLUX-modified DL_POLY) calculation
    can be run. This writes out the DL_POLY input files (CONTROL, CONFIG, FIELD),
    the FFLUX.in settings file, and copies the trained model (``.model``) files into a
    ``model_krig`` subdirectory of the run directory.

    :param run_path: Directory in which to set up (and later run) the DL_FFLUX calculation.
        The directory is created if it does not exist.
    :param model_directory: Directory containing the trained models to use for the
        force field (usually one of the ``6_MODEL/xxx`` subfolders).
    :param starting_geometry: A ``.xyz`` file containing the starting geometry (geometries)
        which is written to the CONFIG file.
    :param ensemble: The DL_POLY ensemble to use, either ``"nvt"`` or ``"nve"``, defaults to ``"nvt"``.
    :param temperature: The temperature of the simulation, defaults to 1.
    :param timestep: The timestep (in ps) of the simulation, defaults to 0.001.
    :param nsteps: The number of timesteps to run the simulation for, defaults to 500.
    :param electrostatics: The electrostatics model written to FFLUX.in when the models
        contain multipole moment data, either ``"ewald"`` or ``"cluster"``, defaults to
        ``"ewald"``. Ignored when the models only contain ``iqa`` (energy) data.
    :param electrostatics_level: The multipole expansion level (L1-L5) for the
        electrostatics directive. If ``None`` (default), it is auto-detected from the
        highest multipole rank present in the models (rank ``l`` maps to level ``L(l+1)``,
        so models up to hexadecapole ``q4x`` give ``L5``). Ignored when there is no
        multipole data.
    :param cell_size: The size (in Angstrom) of the cubic simulation cell written to the
        CONFIG file, defaults to 50.0. Also used to size the SPME Ewald FFT grid for
        multipole runs (~1 grid point per Angstrom). Grown automatically if it would be
        too small for the (molecule-derived) cutoff (a cutoff must be at most half the cell).
    :param cutoff: The real-space cutoff radius (in Angstrom) for the CONTROL ``cutoff`` /
        ``rvdw`` and the FFLUX.in electrostatics ``cut`` directives. If ``None`` (default),
        it is derived from the starting geometry as the largest interatomic distance plus a
        margin, so the whole molecule fits inside the cutoff. FFLUX builds the intramolecular
        interaction cluster within this cutoff and aborts if any atom lies outside it.
    :param cap: Optional force cap (in kT/Angstrom) applied during equilibration, written as
        a ``cap`` line in CONTROL. Useful to stop a far-from-equilibrium run (e.g. one using
        inaccurate FFLUX models) from exploding. ``None`` (default) omits the line.
    :param progress_bar: Whether to show a progress bar while the setup is written out,
        defaults to True. Set to False when calling this in a loop which already has its
        own progress bar (see :func:`submit_dlpoly_fflux_robustness`).
    :return: The path to the run directory which has been set up.
    """

    run_path = Path(run_path)
    mkdir(run_path)

    # the progress bar tracks reading the inputs, writing each of the four DL_POLY/FFLUX
    # input files, and copying the model files. The number of models is not known until
    # they have been read, so the total is extended once that is the case.
    progress = tqdm(
        total=5,
        desc="Reading DL_FFLUX inputs",
        disable=not progress_bar,
    )

    # read the starting geometry which is written to the CONFIG file. A DL_FFLUX run
    # starts from a single geometry (one molecule, matching the single-molecule FIELD
    # file), so if the provided xyz contains multiple geometries only the first is used.
    trajectory = Trajectory(starting_geometry)
    if len(trajectory) > 1:
        ichor.hpc.global_variables.LOGGER.warning(
            f"The starting geometry '{starting_geometry}' contains {len(trajectory)} "
            "geometries; only the first one will be used for the DL_FFLUX CONFIG file."
        )
    # a single-geometry trajectory so that CONFIG matches the FIELD file
    starting_trajectory = trajectory[0:1]
    atoms = trajectory[0]

    # The real-space cutoff must be larger than the molecule's own extent. FFLUX builds
    # the intramolecular interaction cluster within the cutoff and, if any atom lies
    # outside it, prints the offending distance against the cutoff and calls MPI_ABORT.
    # Size the cutoff from the actual geometry: the largest pairwise atom-atom distance
    # (the molecular "diameter") plus a margin, rounded up. Never go below 8.0 A.
    if cutoff is None:
        coords = atoms.coordinates
        diffs = coords[:, None, :] - coords[None, :, :]
        molecule_diameter = float(np.sqrt((diffs**2).sum(axis=-1)).max())
        cutoff = max(8.0, math.ceil(molecule_diameter) + 2.0)

    # DL_POLY requires the cutoff to be at most half the (cubic) cell width; grow the cell
    # if the molecule-derived cutoff would otherwise violate that (also keeps the whole
    # molecule well away from its periodic images).
    min_cell = 2.0 * cutoff + 2.0
    if cell_size < min_cell:
        cell_size = min_cell

    # the models define the chemical system name, which is used to label atoms in the
    # CONFIG file so that DL_FFLUX picks up the correct model file for each atom.
    models = Models(model_directory)
    # one extra step per model file which has to be copied into the run directory
    progress.total = progress.total + len(models)
    progress.update()
    # DL_FFLUX pairs each CONFIG atom label with a model by matching it against
    # "<SystemName>_<AtomName>" built from the model file's "name"/"atom" lines
    # (see fflux_read_models.f90), so the CONFIG labels must use the same system name.
    system_name = models[0].system_name

    # The FFLUX model reader reconstructs each model *file name* in two inconsistent ways:
    #   - the metadata read inserts the property after the FIRST underscore of the CONFIG
    #     label  ->  "<first_token>_iqa_<rest>_<atom>.model"
    #   - the data read (mean/kernel/weights) builds it as
    #     "<SystemName>_iqa_<atom>.model"  (SystemName read from the file's "name" line)
    # When the system name itself contains underscores (e.g. "BZAMID05_MOL_MTD_OUT0") these
    # disagree, so the data-read open silently fails (it is IOSTAT-guarded), nPredPerAtm
    # stays 0, and the mean/kernel/weights are never read -> every IQA energy and force is
    # exactly 0.0 and the molecule flies apart. Removing the underscores makes both
    # constructions collapse to the standard "<system>_<prop>_<atom>.model", so use an
    # underscore-free system name consistently: in the CONFIG atom labels, the copied model
    # file names, AND each model file's own "name" line (which the reader parses back into
    # the file name).
    clean_system_name = system_name.replace("_", "")

    # Electrostatics are only switched on when the models contain multipole moment data.
    # Multipole model properties are named q<l><m> (e.g. "q00" -> rank 0, "q44s" -> rank
    # 4). The highest rank present is the interaction order L', which controls two lines:
    #   - a "Multipolar L'" line in the FIELD file
    #   - an "ewald L(L'+1)" line in FFLUX.in
    # e.g. quadrupole-quadrupole (L'=2) -> "Multipolar 2" + "ewald L3"; a pure-IQA run
    # (no multipole models) omits both lines.
    multipole_ranks = [
        int(match.group(1))
        for prop in models.types
        for match in [re.match(r"q(\d)", prop)]
        if match
    ]
    has_multipole_data = len(multipole_ranks) > 0
    multipolar_order = max(multipole_ranks) if has_multipole_data else None
    if electrostatics_level is None:
        # ewald level is L' + 1 (e.g. L'=2 quadrupole -> ewald L3)
        electrostatics_level = (multipolar_order + 1) if has_multipole_data else 3

    # a multipole (ewald) run needs the SPME Ewald summation set up in CONTROL, otherwise
    # DL_POLY's FFT grid is 0 and it divides by zero in parallel_fft. The FFT grid is set
    # to roughly one point per Angstrom of the (cubic) cell, rounded up to an even number.
    spme_sum = None
    if has_multipole_data:
        grid = max(int(cell_size), 2)
        if grid % 2 != 0:
            grid += 1
        spme_sum = f"0.00001 {grid} {grid} {grid}"

    # FFLUX-specific settings live in FFLUX.in, so the inline fflux directives are
    # omitted from the CONTROL file (fflux_cluster / fflux_print set to None)
    progress.set_description("Writing CONTROL file")
    DlPolyControl(
        system_name=clean_system_name,
        path=run_path / "CONTROL",
        ensemble=ensemble,
        temperature=temperature,
        timestep=timestep,
        steps=nsteps,
        cutoff=cutoff,
        rvwd=cutoff,
        fflux_cluster=None,
        fflux_print=None,
        spme_sum=spme_sum,
        cap=cap,
    ).write()
    progress.update()

    progress.set_description("Writing CONFIG file")
    DlPolyConfig(
        system_name=clean_system_name,
        trajectory=starting_trajectory,
        path=run_path / "CONFIG",
        cell_size=cell_size,
    ).write()
    progress.update()

    progress.set_description("Writing FIELD file")
    DlPolyField(
        system_name=clean_system_name,
        atoms=atoms,
        path=run_path / "FIELD",
        multipolar=multipolar_order,
        # for multipole runs, exclude ALL intramolecular pairs from the electrostatics
        # (FFLUX handles the intramolecular energy via the IQA models) - otherwise the
        # explicit multipole electrostatics double-counts intramolecular interactions and
        # diverges as atoms approach, blowing up the trajectory.
        all_pairs_bonds=has_multipole_data,
    ).write()
    progress.update()

    progress.set_description("Writing FFLUX.in file")
    DlPolyFFLUXInput(
        path=run_path / "FFLUX.in",
        title=clean_system_name,
        electrostatics=electrostatics if has_multipole_data else None,
        electrostatics_level=electrostatics_level,
        electrostatics_cutoff=cutoff,
    ).write()
    progress.update()

    # a multipole run also needs an MPOLES file so DL_POLY can allocate the multipole
    # moment arrays (the values are dummies overwritten by the FFLUX predictions)
    if has_multipole_data:
        progress.total = progress.total + 1
        progress.set_description("Writing MPOLES file")
        DlPolyMpoles(
            system_name=clean_system_name,
            atoms=atoms,
            path=run_path / "MPOLES",
        ).write()
        progress.update()

    # copy the model files into a "model_krig" subdirectory (where DL_FFLUX looks for the
    # trained models), named in the standard FFLUX layout "<system>_<prop>_<atom>.model"
    # (property token right after the system name). With the underscore-free system name the
    # reader's metadata-read and data-read filename constructions agree on this name, so the
    # mean/kernel/weights are actually read. Each file's own "name" line is rewritten to the
    # underscore-free system name too, because the reader parses that line back into the file
    # name it opens for the data read.
    progress.set_description("Copying model files")
    model_krig_dir = run_path / "model_krig"
    mkdir(model_krig_dir)
    for model in models:
        new_name = (
            f"{clean_system_name}_{model.prop}_{model.atom_name}{model.path.suffix}"
        )
        _copy_model_with_clean_system_name(
            model.path,
            model_krig_dir / new_name,
            system_name,
            clean_system_name,
        )
        progress.update()

    progress.set_description("DL_FFLUX setup complete")
    progress.close()

    return run_path


def submit_dlpoly_fflux(
    run_path: Union[str, Path],
    model_directory: Union[str, Path],
    starting_geometry: Union[str, Path],
    ensemble: str = "nvt",
    temperature: int = 1,
    timestep: float = 0.001,
    nsteps: int = 500,
    ncores: int = 1,
    electrostatics: str = "ewald",
    electrostatics_level: Optional[int] = None,
    cell_size: float = 50.0,
    cutoff: Optional[float] = None,
    cap: Optional[float] = None,
    executable_path: Optional[Union[str, Path]] = None,
) -> JobID:
    """Sets up and submits a DL_FFLUX (FFLUX-modified DL_POLY) calculation to a compute node.

    See :func:`write_dlpoly_fflux_setup` for a description of the setup arguments.

    :param ncores: The number of cores to use for the DL_FFLUX job, defaults to 1.
    :param executable_path: An optional path to the DL_FFLUX (DLPOLY.Z) executable which
        overrides the configured ``software.dlpoly.executable_path``. If ``None`` (default),
        the configured executable path is used.
    :return: An object containing information for the submitted job.
    :rtype: ichor.hpc.batch_system.jobs.JobID
    """

    run_path = write_dlpoly_fflux_setup(
        run_path=run_path,
        model_directory=model_directory,
        starting_geometry=starting_geometry,
        ensemble=ensemble,
        temperature=temperature,
        timestep=timestep,
        nsteps=nsteps,
        electrostatics=electrostatics,
        electrostatics_level=electrostatics_level,
        cell_size=cell_size,
        cutoff=cutoff,
        cap=cap,
    )

    with SubmissionScript(
        ichor.hpc.global_variables.SCRIPT_NAMES["dlpoly"], ncores=ncores
    ) as submission_script:
        submission_script.add_command(DlpolyCommand(executable_path, run_path))

    return submission_script.submit()


def submit_dlpoly_fflux_robustness(
    base_path: Union[str, Path],
    model_directory: Union[str, Path],
    seed_trajectory: Union[str, Path],
    nseeds: int,
    ensemble: str = "nvt",
    temperature: int = 1,
    timestep: float = 0.001,
    nsteps: int = 500,
    ncores: int = 1,
    electrostatics: str = "ewald",
    electrostatics_level: Optional[int] = None,
    cell_size: float = 50.0,
    cutoff: Optional[float] = None,
    cap: Optional[float] = None,
    executable_path: Optional[Union[str, Path]] = None,
) -> JobID:
    """Sets up and submits a DL_FFLUX model-robustness check.

    A robustness check runs several independent DL_FFLUX simulations, each started from a
    different (diverse) seed geometry, to probe how stable the model is across the
    accessible configuration space (e.g. checking for the trajectory "exploding" or
    "imploding"). The first ``nseeds`` geometries are taken, in order, from the supplied
    (usually diversity-sampled) trajectory. Each seed gets its own ``RUN<i>`` directory
    under ``base_path``, and all runs are submitted together as a single job array.

    :param base_path: Base directory in which the per-seed ``RUN<i>`` directories are created.
    :param model_directory: Directory containing the trained models (e.g. a ``6_MODEL/xxx`` subfolder).
    :param seed_trajectory: A ``.xyz`` trajectory (usually the diversity-sampled set) from
        which the seed geometries are taken in order.
    :param nseeds: The number of seed geometries (and hence separate runs) to set up. If
        this exceeds the number of geometries available, all available geometries are used.
    :param ensemble: The DL_POLY ensemble to use, either ``"nvt"`` or ``"nve"``, defaults to ``"nvt"``.
    :param temperature: The temperature of the simulations, defaults to 1.
    :param timestep: The timestep (in ps) of the simulations, defaults to 0.001.
    :param nsteps: The number of timesteps to run each simulation for, defaults to 500.
    :param ncores: The number of cores to use per run, defaults to 1.
    :param electrostatics: The electrostatics model written to FFLUX.in when the models
        contain multipole moment data, defaults to ``"ewald"``.
    :param electrostatics_level: The multipole expansion level (L1-L5). If ``None``
        (default), it is auto-detected from the highest multipole rank present in the models.
    :param executable_path: An optional path to the DL_FFLUX (DLPOLY.Z) executable which
        overrides the configured ``software.dlpoly.executable_path``. If ``None`` (default),
        the configured executable path is used.
    :return: An object containing information for the submitted (array) job.
    :rtype: ichor.hpc.batch_system.jobs.JobID
    """

    base_path = Path(base_path)
    mkdir(base_path)

    trajectory = Trajectory(seed_trajectory)
    # take the first nseeds geometries in order, but never more than are available
    nseeds = min(nseeds, len(trajectory))

    run_paths = []
    # one progress bar over the seeds rather than a separate bar per run directory
    for i in tqdm(range(nseeds), desc="Setting up DL_FFLUX run directories"):
        run_path = base_path / f"RUN{i}"
        mkdir(run_path)

        # materialise this seed geometry as an xyz inside the run directory, then
        # use the standard single-run setup to write CONTROL/CONFIG/FIELD/FFLUX.in
        seed_xyz = run_path / "seed.xyz"
        seed = Trajectory(seed_xyz)
        seed.add(trajectory[i])
        seed.write()

        write_dlpoly_fflux_setup(
            run_path=run_path,
            model_directory=model_directory,
            starting_geometry=seed_xyz,
            ensemble=ensemble,
            temperature=temperature,
            timestep=timestep,
            nsteps=nsteps,
            electrostatics=electrostatics,
            electrostatics_level=electrostatics_level,
            cell_size=cell_size,
            cutoff=cutoff,
            cap=cap,
            progress_bar=False,
        )
        run_paths.append(run_path)

    # add one DL_POLY command per run directory to a single submission script; ichor
    # groups these same-type commands into a job array (one array task per run)
    with SubmissionScript(
        ichor.hpc.global_variables.SCRIPT_NAMES["dlpoly"], ncores=ncores
    ) as submission_script:
        for run_path in run_paths:
            submission_script.add_command(DlpolyCommand(executable_path, run_path))

    return submission_script.submit()


def submit_dlpoly_fflux_stability_check(
    base_path: Union[str, Path],
    reference_geometry: Union[str, Path],
    report_path: Union[str, Path] = "STABILITY-REPORT.txt",
    run_directory_glob: str = "RUN*",
    stride: int = 1000,
    explosion_factor: float = 1.35,
    implosion_factor: float = 1.5,
    max_timesteps: Optional[int] = None,
    timestep: float = 0.001,
    ncores: int = 1,
) -> JobID:
    """Submits a stability check of finished DL_FFLUX runs to a compute node.

    The HISTORY files of a robustness check are usually far too large to be analysed
    comfortably on a login node, so the analysis (see
    :class:`ichor.core.analysis.DlpolyStabilityCheck`) can be run as a job instead.

    :param base_path: Directory containing the run directories to check.
    :param reference_geometry: Path to the reference geometry (``.xyz`` or ``.gjf``),
        usually the optimised geometry, whose bond lengths define an intact molecule.
    :param report_path: Path of the report file to write, defaults to
        ``"STABILITY-REPORT.txt"``.
    :param run_directory_glob: Glob matching the run directories inside ``base_path``,
        defaults to ``"RUN*"``.
    :param stride: How often (in timesteps) each trajectory is checked in the first
        pass, defaults to 1000.
    :param explosion_factor: A bond counts as exploded when it is longer than this factor
        times its reference length, defaults to 1.35.
    :param implosion_factor: A bond counts as imploded when it is shorter than its
        reference length divided by this factor, defaults to 1.5.
    :param max_timesteps: The number of timesteps each run was meant to last for, used
        for the robustness. If None (default), the longest run in the set is used.
    :param timestep: The timestep (in ps) the simulations were run with, used to convert
        stabilities into times, defaults to 0.001.
    :param ncores: The number of cores to use for the job, defaults to 1.
    :return: An object containing information for the submitted job.
    :rtype: ichor.hpc.batch_system.jobs.JobID
    """

    base_path = Path(base_path).absolute()
    reference_geometry = Path(reference_geometry).absolute()

    # this gets executed as `python -c ...` on the compute node
    text_list = [
        "from pathlib import Path",
        "from ichor.core.analysis import DlpolyStabilityCheck",
        f"runs = sorted(Path(r'{base_path}').glob('{run_directory_glob}'))",
        "check = DlpolyStabilityCheck("
        f"r'{reference_geometry}', runs, stride={stride},"
        f" explosion_factor={explosion_factor}, implosion_factor={implosion_factor})",
        f"check.write_report(r'{Path(report_path).absolute()}',"
        f" max_timesteps={max_timesteps}, timestep_length={timestep})",
    ]

    return submit_free_flow_python_command_on_compute(
        text_list,
        ichor.hpc.global_variables.SCRIPT_NAMES["stability_check"],
        ncores=ncores,
    )
