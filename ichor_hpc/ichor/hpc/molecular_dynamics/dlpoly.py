import math
import os
import re
import shutil
from pathlib import Path
from typing import List, Optional, Union

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

# the directory DL_FFLUX reads the trained models from. It is looked for relative to the
# directory a run is executed in, so every run directory needs one (either a real
# directory of model files or, as set up here, a link to a shared one).
MODEL_DIRECTORY_NAME = "model_krig"

# file written into a shared model directory recording the model directory the models in
# it were copied from, so that runs which are set up into the same base path later can
# tell whether they are allowed to share the models which are already there
MODEL_SOURCE_FILE_NAME = ".ichor_model_source"

# prefix of the per-run directories created inside a DL_FFLUX base path
RUN_DIRECTORY_PREFIX = "RUN"

# prefix of the per-geometry directories of a set of DL_FFLUX single point calculations.
# These are named differently from the RUN<i> directories of a simulation so that the two
# can be told apart (e.g. by the stability check, which only makes sense for simulations).
SINGLE_POINT_DIRECTORY_PREFIX = "POINT"

# the number of timesteps which makes a DL_FFLUX run a single point calculation: DL_POLY
# evaluates the energies and forces of the configuration it was given and stops without
# ever moving an atom
SINGLE_POINT_NSTEPS = 0


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


def _model_file_name(clean_system_name: str, model) -> str:
    """Returns the file name a model is copied to, in the standard FFLUX layout
    ``<system>_<prop>_<atom>.model`` (property token right after the system name)."""
    return f"{clean_system_name}_{model.prop}_{model.atom_name}{model.path.suffix}"


def write_dlpoly_fflux_model_directory(
    model_directory: Union[str, Path],
    parent_path: Union[str, Path],
    models: Optional[Models] = None,
    progress: Optional[tqdm] = None,
) -> Path:
    """Copies the trained models into a ``model_krig`` directory inside ``parent_path``,
    named in the layout the FFLUX model reader expects, and returns the path of that
    directory.

    Model files are large and a set of DL_FFLUX runs (a robustness check, or several
    single runs set up into the same place) all use the same models, so the copy is made
    once per base directory and the run directories only link to it (see
    :func:`write_dlpoly_fflux_setup`). An existing directory is therefore reused rather
    than copied over again: the model directory it was copied from is recorded in a
    ``.ichor_model_source`` file, and only the model files which are not there yet are
    copied.

    :param model_directory: Directory containing the trained models to copy (usually one
        of the ``6_MODEL/xxx`` subfolders).
    :param parent_path: Directory to create the ``model_krig`` directory in. This is the
        base directory holding the run directories, not a run directory itself (unless the
        models are deliberately not being shared).
    :param models: The already read models of ``model_directory``. Reading the models is
        by far the most expensive part of setting a run up, so a caller setting up several
        runs from the same models should read them once and pass them in here. If ``None``
        (default), they are read from ``model_directory``.
    :param progress: An optional progress bar to advance once per copied model file, whose
        total already accounts for them. If ``None`` (default), a progress bar of its own
        is shown while the models are copied.
    :raises ValueError: If the directory already holds models copied from a *different*
        model directory, as overwriting those would silently change the force field of the
        runs which are already set up (and possibly running) alongside it.
    :return: The path to the ``model_krig`` directory the models were copied into.
    """

    # the source is recorded (and compared) in canonical form, so that the same directory
    # written differently (e.g. through a relative path) is recognised as the same one
    model_directory = Path(model_directory).resolve()
    parent_path = Path(parent_path)
    models = models if models is not None else Models(model_directory)

    model_krig_dir = parent_path / MODEL_DIRECTORY_NAME
    source_file = model_krig_dir / MODEL_SOURCE_FILE_NAME

    previous_source = None
    if source_file.is_file():
        previous_source = Path(source_file.read_text().strip()).resolve()

    if previous_source is not None and previous_source != model_directory:
        raise ValueError(
            f"The models in '{model_krig_dir}' were copied from '{previous_source}', but "
            f"this run uses the models in '{model_directory}'. The runs inside "
            f"'{parent_path}' all share one set of models, so setting this run up here "
            "would change the force field of the runs which are already set up. Please "
            "use a different base path for a different set of models."
        )

    # models which are already there but whose origin is not recorded (e.g. copied by a
    # version of ichor which did not share them yet) cannot be assumed to be the ones
    # asked for, so they are copied over rather than reused
    unknown_models_present = previous_source is None and any(
        model_krig_dir.glob("*.model")
    )
    if unknown_models_present:
        ichor.hpc.global_variables.LOGGER.warning(
            f"The models already in '{model_krig_dir}' do not record which model "
            f"directory they came from, so they are being overwritten with the models "
            f"in '{model_directory}'."
        )

    mkdir(model_krig_dir)

    # the models define the chemical system name. The FFLUX model reader reconstructs each
    # model file name from the system name it parses out of the file, so both the copied
    # file names and the "name" line inside them use an underscore-free system name (see
    # write_dlpoly_fflux_setup for why).
    system_name = models[0].system_name
    clean_system_name = system_name.replace("_", "")

    own_progress = progress is None
    if own_progress:
        progress = tqdm(total=len(models), desc="Copying model files")

    for model in models:
        destination = model_krig_dir / _model_file_name(clean_system_name, model)
        if unknown_models_present or not destination.exists():
            _copy_model_with_clean_system_name(
                model.path,
                destination,
                system_name,
                clean_system_name,
            )
        progress.update()

    if own_progress:
        progress.close()

    source_file.write_text(f"{model_directory}\n")

    return model_krig_dir


def _link_shared_model_directory(shared_model_directory: Path, run_path: Path) -> Path:
    """Points a run directory's ``model_krig`` at a shared model directory, so that the
    (large) model files only exist once per set of runs.

    :param shared_model_directory: The shared directory holding the copied model files,
        as written by :func:`write_dlpoly_fflux_model_directory`.
    :param run_path: The run directory to create the link in.
    :return: The path of the created ``model_krig`` link.
    """

    link_path = run_path / MODEL_DIRECTORY_NAME

    if link_path.is_symlink():
        # a link left over from setting the same run up before could point somewhere else
        link_path.unlink()
    elif link_path.is_dir():
        # models copied into the run directory itself (by an earlier version of ichor, or
        # by a setup which could not make links). The run is being set up from scratch, so
        # these are replaced by the link to the shared models.
        ichor.hpc.global_variables.LOGGER.info(
            f"Replacing the copied models in '{link_path}' with a link to "
            f"'{shared_model_directory}'."
        )
        shutil.rmtree(link_path)

    # a relative target keeps the links working when the whole set of runs is moved
    # (e.g. copied off the cluster) as long as the shared directory comes along with it
    target = Path(
        os.path.relpath(Path(shared_model_directory).absolute(), run_path.absolute())
    )

    try:
        link_path.symlink_to(target, target_is_directory=True)
    except OSError:
        # not every platform / filesystem allows making symbolic links (e.g. Windows
        # without developer mode), in which case the models have to be copied after all
        ichor.hpc.global_variables.LOGGER.warning(
            f"Could not link '{link_path}' to '{shared_model_directory}', "
            "copying the model files into the run directory instead."
        )
        shutil.copytree(shared_model_directory, link_path)

    return link_path


def next_run_directory(
    base_path: Union[str, Path], prefix: str = RUN_DIRECTORY_PREFIX
) -> Path:
    """Returns the path of the next free run directory inside a DL_FFLUX base path, i.e.
    one past the highest ``RUN<i>`` index already in it (``RUN0`` if there are none).

    Runs set up into the same base path share its model directory, so several of them can
    live side by side; numbering from the runs which are already there keeps a new run
    from overwriting them.

    :param base_path: The base directory holding the run directories.
    :param prefix: The prefix of the run directory names, defaults to ``"RUN"``.
    """

    base_path = Path(base_path)

    indices: List[int] = []
    for directory in base_path.glob(f"{prefix}*"):
        index = directory.name[len(prefix) :]
        if directory.is_dir() and index.isdigit():
            indices.append(int(index))

    return base_path / f"{prefix}{max(indices) + 1 if indices else 0}"


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
    models: Optional[Models] = None,
    shared_model_directory: Optional[Union[str, Path]] = None,
    progress_bar: bool = True,
) -> Path:
    """Sets up a directory from which a DL_FFLUX (FFLUX-modified DL_POLY) calculation
    can be run. This writes out the DL_POLY input files (CONTROL, CONFIG, FIELD),
    the FFLUX.in settings file, and gives the run directory the ``model_krig``
    subdirectory that DL_FFLUX reads the trained model (``.model``) files from - either a
    link to a shared copy of the models (see ``shared_model_directory``) or, failing that,
    a copy of its own.

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
    :param models: The already read models of ``model_directory``. Reading the models is by
        far the most expensive part of setting a run up, so a caller setting up several runs
        from the same models should read them once and pass them in here. If ``None``
        (default), they are read from ``model_directory``.
    :param shared_model_directory: An existing directory holding the models already copied
        out in the FFLUX layout (see :func:`write_dlpoly_fflux_model_directory`), which the
        run directory's ``model_krig`` is linked to instead of getting a copy of its own.
        Model files are large, so runs sharing one copy saves a lot of disk space. If
        ``None`` (default), the models are copied into the run directory itself.
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
    models = models if models is not None else Models(model_directory)
    # linking to a shared copy of the models is one step, copying them is one per model file
    progress.total = progress.total + (1 if shared_model_directory else len(models))
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

    # DL_FFLUX reads the trained models from a "model_krig" subdirectory of the directory
    # the run is executed in. The model files are named in the standard FFLUX layout
    # "<system>_<prop>_<atom>.model" (property token right after the system name); with the
    # underscore-free system name the reader's metadata-read and data-read filename
    # constructions agree on this name, so the mean/kernel/weights are actually read.
    if shared_model_directory:
        # the models have already been copied out for the whole set of runs, so this run
        # only needs to point at them
        progress.set_description("Linking model files")
        _link_shared_model_directory(Path(shared_model_directory), run_path)
        progress.update()
    else:
        progress.set_description("Copying model files")
        write_dlpoly_fflux_model_directory(
            model_directory, run_path, models=models, progress=progress
        )

    progress.set_description("DL_FFLUX setup complete")
    progress.close()

    return run_path


def submit_dlpoly_fflux(
    base_path: Union[str, Path],
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

    The calculation is set up in its own ``RUN<i>`` directory inside ``base_path``, next to
    the ``model_krig`` directory the models are copied into, which every run under the same
    base path shares (model files are large, so copying them per run fills up disk quotas
    very quickly). Submitting another calculation with the same base path therefore adds a
    run rather than overwriting the one that is already there: the first is set up in
    ``RUN0``, the next in ``RUN1``, and so on, each only linking to the shared models.

    See :func:`write_dlpoly_fflux_setup` for a description of the setup arguments.

    :param base_path: Base directory to create the run directory (and the shared model
        directory) in. The directory is created if it does not exist.
    :param ncores: The number of cores to use for the DL_FFLUX job, defaults to 1.
    :param executable_path: An optional path to the DL_FFLUX (DLPOLY.Z) executable which
        overrides the configured ``software.dlpoly.executable_path``. If ``None`` (default),
        the configured executable path is used.
    :raises ValueError: If the base path already holds models copied from a different model
        directory, see :func:`write_dlpoly_fflux_model_directory`.
    :return: An object containing information for the submitted job.
    :rtype: ichor.hpc.batch_system.jobs.JobID
    """

    base_path = Path(base_path)
    mkdir(base_path)

    # read the models once, both to copy them out and to set the run up with
    models = Models(model_directory)
    # the models are shared by every run under the base path, so they are only copied if
    # they are not already there from a previous run
    shared_model_directory = write_dlpoly_fflux_model_directory(
        model_directory, base_path, models=models
    )

    run_path = next_run_directory(base_path)

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
        models=models,
        shared_model_directory=shared_model_directory,
    )
    ichor.hpc.global_variables.LOGGER.info(f"DL_FFLUX run set up in {run_path}")

    with SubmissionScript(
        ichor.hpc.global_variables.SCRIPT_NAMES["dlpoly"], ncores=ncores
    ) as submission_script:
        submission_script.add_command(DlpolyCommand(executable_path, run_path))

    return submission_script.submit()


def submit_dlpoly_fflux_trajectory(
    base_path: Union[str, Path],
    model_directory: Union[str, Path],
    trajectory_path: Union[str, Path],
    ngeometries: Optional[int] = None,
    run_directory_prefix: str = RUN_DIRECTORY_PREFIX,
    geometry_file_name: str = "geometry.xyz",
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
    """Sets up and submits one DL_FFLUX calculation per geometry of a trajectory.

    The geometries are taken in order from the trajectory and each gets its own
    ``<prefix><i>`` directory under ``base_path``, all of which are submitted together as
    a single job array. This is what a robustness check
    (:func:`submit_dlpoly_fflux_robustness`) and a set of single points
    (:func:`submit_dlpoly_fflux_single_points`) are both made of; they differ in how long
    the runs last for and in what the run directories are called.

    Every run uses the same models, so these are copied out once into a ``model_krig``
    directory in ``base_path`` which the run directories only link to (copying the model
    files per run fills up disk quotas very quickly).

    :param base_path: Base directory in which the per-geometry run directories and the
        shared ``model_krig`` directory are created.
    :param model_directory: Directory containing the trained models (e.g. a ``6_MODEL/xxx`` subfolder).
    :param trajectory_path: A ``.xyz`` trajectory from which the geometries are taken in order.
    :param ngeometries: The number of geometries (and hence separate runs) to set up. If
        this exceeds the number of geometries available, or is ``None`` (default), all of
        the geometries in the trajectory are used.
    :param run_directory_prefix: The prefix of the per-geometry run directory names,
        defaults to ``"RUN"`` (so ``RUN0``, ``RUN1``, ...).
    :param geometry_file_name: The name the geometry of a run is written out under inside
        its run directory, defaults to ``"geometry.xyz"``.
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
    :raises ValueError: If the base path already holds models copied from a different model
        directory, see :func:`write_dlpoly_fflux_model_directory`.
    :return: An object containing information for the submitted (array) job.
    :rtype: ichor.hpc.batch_system.jobs.JobID
    """

    base_path = Path(base_path)
    mkdir(base_path)

    trajectory = Trajectory(trajectory_path)
    # take the geometries in order, but never more than the trajectory holds
    ngeometries = (
        len(trajectory) if ngeometries is None else min(ngeometries, len(trajectory))
    )

    # every run is set up from the same models, so they are read (the most expensive part
    # of setting a run up) and copied out only once, and each run directory then just
    # links to the copy
    models = Models(model_directory)
    shared_model_directory = write_dlpoly_fflux_model_directory(
        model_directory, base_path, models=models
    )

    run_paths = []
    # one progress bar over the geometries rather than a separate bar per run directory
    for i in tqdm(range(ngeometries), desc="Setting up DL_FFLUX run directories"):
        run_path = base_path / f"{run_directory_prefix}{i}"
        mkdir(run_path)

        # materialise this geometry as an xyz inside the run directory, then
        # use the standard single-run setup to write CONTROL/CONFIG/FIELD/FFLUX.in
        geometry_path = run_path / geometry_file_name
        geometry = Trajectory(geometry_path, read_geometries=False)
        geometry.add(trajectory[i])
        geometry.write()

        write_dlpoly_fflux_setup(
            run_path=run_path,
            model_directory=model_directory,
            starting_geometry=geometry_path,
            ensemble=ensemble,
            temperature=temperature,
            timestep=timestep,
            nsteps=nsteps,
            electrostatics=electrostatics,
            electrostatics_level=electrostatics_level,
            cell_size=cell_size,
            cutoff=cutoff,
            cap=cap,
            models=models,
            shared_model_directory=shared_model_directory,
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
    under ``base_path`` (sharing one copy of the models, see
    :func:`submit_dlpoly_fflux_trajectory`), and all runs are submitted together as a
    single job array.

    :param base_path: Base directory in which the per-seed ``RUN<i>`` directories and the
        shared ``model_krig`` directory are created.
    :param model_directory: Directory containing the trained models (e.g. a ``6_MODEL/xxx`` subfolder).
    :param seed_trajectory: A ``.xyz`` trajectory (usually the diversity-sampled set) from
        which the seed geometries are taken in order.
    :param nseeds: The number of seed geometries (and hence separate runs) to set up. If
        this exceeds the number of geometries available, all available geometries are used.
    :param nsteps: The number of timesteps to run each simulation for, defaults to 500.

    See :func:`submit_dlpoly_fflux_trajectory` for the remaining arguments.

    :raises ValueError: If the base path already holds models copied from a different model
        directory, see :func:`write_dlpoly_fflux_model_directory`.
    :return: An object containing information for the submitted (array) job.
    :rtype: ichor.hpc.batch_system.jobs.JobID
    """

    return submit_dlpoly_fflux_trajectory(
        base_path=base_path,
        model_directory=model_directory,
        trajectory_path=seed_trajectory,
        ngeometries=nseeds,
        run_directory_prefix=RUN_DIRECTORY_PREFIX,
        geometry_file_name="seed.xyz",
        ensemble=ensemble,
        temperature=temperature,
        timestep=timestep,
        nsteps=nsteps,
        ncores=ncores,
        electrostatics=electrostatics,
        electrostatics_level=electrostatics_level,
        cell_size=cell_size,
        cutoff=cutoff,
        cap=cap,
        executable_path=executable_path,
    )


def submit_dlpoly_fflux_single_points(
    base_path: Union[str, Path],
    model_directory: Union[str, Path],
    trajectory_path: Union[str, Path],
    ngeometries: Optional[int] = None,
    ensemble: str = "nvt",
    temperature: int = 1,
    timestep: float = 0.001,
    nsteps: int = SINGLE_POINT_NSTEPS,
    ncores: int = 1,
    electrostatics: str = "ewald",
    electrostatics_level: Optional[int] = None,
    cell_size: float = 50.0,
    cutoff: Optional[float] = None,
    executable_path: Optional[Union[str, Path]] = None,
) -> JobID:
    """Sets up and submits a DL_FFLUX single point calculation for every geometry of a
    trajectory.

    This is the quick way of getting the FFLUX energies (and forces) of a whole set of
    geometries, e.g. to compare the predictions of the models against the reference
    (Gaussian/AIMAll) values the geometries were labelled with. No dynamics is run: each
    geometry gets a run of ``SINGLE_POINT_NSTEPS`` (0) timesteps, which makes DL_FFLUX
    evaluate the geometry it was given and stop.

    Each geometry gets its own ``POINT<i>`` directory under ``base_path``, numbered in the
    order the geometries appear in the trajectory, and all of them are submitted together
    as a single job array. The run directories are named differently from those of a
    robustness check (``RUN<i>``) so that a stability check of the same base path does not
    pick up the single points, which have no trajectory to be stable over.

    :param base_path: Base directory in which the per-geometry ``POINT<i>`` directories and
        the shared ``model_krig`` directory are created.
    :param model_directory: Directory containing the trained models (e.g. a ``6_MODEL/xxx`` subfolder).
    :param trajectory_path: A ``.xyz`` file holding the geometries to calculate.
    :param ngeometries: The number of geometries (taken in order) to calculate. If this
        exceeds the number of geometries in the file, or is ``None`` (default), every
        geometry in the file is calculated.
    :param nsteps: The number of timesteps of each run, defaults to
        ``SINGLE_POINT_NSTEPS`` (0), i.e. a single point calculation.

    See :func:`submit_dlpoly_fflux_trajectory` for the remaining arguments.

    :raises ValueError: If the base path already holds models copied from a different model
        directory, see :func:`write_dlpoly_fflux_model_directory`.
    :return: An object containing information for the submitted (array) job.
    :rtype: ichor.hpc.batch_system.jobs.JobID
    """

    return submit_dlpoly_fflux_trajectory(
        base_path=base_path,
        model_directory=model_directory,
        trajectory_path=trajectory_path,
        ngeometries=ngeometries,
        run_directory_prefix=SINGLE_POINT_DIRECTORY_PREFIX,
        geometry_file_name="geometry.xyz",
        ensemble=ensemble,
        temperature=temperature,
        timestep=timestep,
        nsteps=nsteps,
        ncores=ncores,
        electrostatics=electrostatics,
        electrostatics_level=electrostatics_level,
        cell_size=cell_size,
        cutoff=cutoff,
        # a run which does not move cannot explode, so there is nothing to cap
        cap=None,
        executable_path=executable_path,
    )


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
