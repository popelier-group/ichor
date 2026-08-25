"""Extraction of geometries from a DL_FFLUX (DL_POLY) ``HISTORY`` trajectory.

A finished DL_FFLUX run writes every timestep it was told to print into its ``HISTORY``
file, which is both far larger than the geometries which are actually wanted out of it
(a training set is built from a few thousand of them, not from every timestep of a
multi-million timestep run) and far too large to read in with
:class:`ichor.core.files.DlPolyHistory`, which holds the whole trajectory in memory.

The trajectory is therefore streamed here and each wanted geometry is written straight
out to an ``.xyz`` file as it is read, so that what is held in memory is one timestep
rather than the run. Timesteps containing binary data, which DL_POLY occasionally writes
into HISTORY files, are skipped, as they are by the stability check in
:mod:`ichor.core.analysis.dlpoly.stability_check`.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List, Optional, Tuple, Union

__all__ = ["subsample_history", "SubsampledTrajectory"]


@dataclass
class SubsampledTrajectory:
    """What was written out of a HISTORY file by :func:`subsample_history`.

    :param history_path: The HISTORY file which was read.
    :param output_path: The .xyz file which was written, or None if no geometry matched
        the selection, in which case nothing was written at all.
    :param natoms: The number of atoms in each written geometry (0 if none were written).
    :param atom_names: The names of those atoms, as they are written in the HISTORY file.
    :param ngeometries: The number of geometries which were written.
    :param first_timestep: The first timestep which was written, or None.
    :param last_timestep: The last timestep which was written, or None.
    :param nframes_read: The number of timesteps which were read (and not necessarily
        written) out of the HISTORY file.
    :param nframes_skipped: The number of timesteps which were wanted but could not be
        used, because they contain binary data or a different number of atoms.
    """

    history_path: Path
    output_path: Optional[Path]
    natoms: int = 0
    atom_names: List[str] = field(default_factory=list)
    ngeometries: int = 0
    first_timestep: Optional[int] = None
    last_timestep: Optional[int] = None
    nframes_read: int = 0
    nframes_skipped: int = 0


def _iter_history_frames(f) -> Iterator[Tuple[int, int, List[str]]]:
    """Splits an open HISTORY file into ``(timestep, natoms, lines)``, without parsing
    the coordinates, so that only the timesteps which are wanted are paid for.

    The two header lines at the top of a HISTORY file are skipped implicitly, as
    everything before the first ``timestep`` record is ignored. Truncated timesteps (the
    last one of a run which is still going, for instance) and timesteps containing the
    binary which DL_POLY sometimes writes into the file are not yielded.

    :param f: The open HISTORY file.
    """

    line = f.readline()
    while line:

        record = line.split()
        # record = timestep ntimestep natoms keytrj imcon timestep_length time
        if not record or record[0] != "timestep" or len(record) < 5:
            line = f.readline()
            continue

        try:
            timestep = int(record[1])
            natoms = int(record[2])
            trajectory_key = int(record[3])
        except ValueError:
            line = f.readline()
            continue

        # 3 unit cell lines, then per atom a name line, a coordinate line and,
        # depending on the trajectory key, a velocity and/or a force line
        nlines = 3 + natoms * (2 + trajectory_key)

        frame_lines = []
        line = f.readline()
        while line and len(frame_lines) < nlines:
            # a new timestep record before the current one is complete means the current
            # one is truncated, so resynchronise on the new record
            if line.split()[:1] == ["timestep"]:
                break
            frame_lines.append(line)
            line = f.readline()

        if len(frame_lines) != nlines:
            continue

        # DL_POLY sometimes writes binary into the HISTORY file, corrupting a timestep
        if any("\x00" in frame_line for frame_line in frame_lines):
            continue

        yield timestep, natoms, frame_lines


def _parse_geometry(
    frame_lines: List[str], natoms: int
) -> Optional[Tuple[List[str], List[Tuple[float, float, float]]]]:
    """Parses the atom names and coordinates out of the lines of a single timestep.

    :param frame_lines: The lines of the timestep, i.e. the 3 unit cell lines followed by
        one block per atom.
    :param natoms: The number of atoms the timestep holds.
    :return: The atom names and their coordinates, or None if the timestep could not be
        read.
    """

    # 3 unit cell lines, then blocks of (name, coordinates, [velocity], [force])
    lines_per_atom = (len(frame_lines) - 3) // natoms

    names = []
    coordinates = []

    for atom_index in range(natoms):
        name_line = frame_lines[3 + atom_index * lines_per_atom]
        coordinate_line = frame_lines[3 + atom_index * lines_per_atom + 1]
        name_record = name_line.split()
        coordinate_record = coordinate_line.split()
        if not name_record or len(coordinate_record) < 3:
            return None
        try:
            x, y, z = (float(c) for c in coordinate_record[:3])
        except ValueError:
            return None
        names.append(name_record[0])
        coordinates.append((x, y, z))

    return names, coordinates


def _geometry_str(
    names: List[str], coordinates: List[Tuple[float, float, float]], timestep: int
) -> str:
    """Formats one timestep as a geometry of an .xyz trajectory, with the timestep it
    came from written on the comment line so that it can be traced back to the run."""

    lines = [f"{len(names)}\n", f"timestep: {timestep}\n"]
    for name, (x, y, z) in zip(names, coordinates):
        lines.append(f"{name} {x:16.12f} {y:16.12f} {z:16.12f}\n")

    return "".join(lines)


def subsample_history(
    history_path: Union[str, Path],
    output_path: Union[str, Path],
    stride: int = 1,
    min_step: int = 0,
    max_step: Optional[int] = None,
    exact_step: Optional[int] = None,
    last_step_only: bool = False,
) -> SubsampledTrajectory:
    """Writes geometries of a DL_FFLUX ``HISTORY`` trajectory out as an ``.xyz`` file.

    The HISTORY file is streamed rather than read in, so the memory this needs is that of
    a single timestep however long the run was, and only the timesteps which are wanted
    are parsed.

    Which timesteps are written is decided by the timestep numbers themselves rather than
    by their position in the file, so that the geometries can be traced back to the run
    (and so that the same selection means the same thing for a run whose HISTORY was
    written every timestep and one whose was written every hundredth). The selections are
    tried in the order below, i.e. ``last_step_only`` overrides ``exact_step``, which
    overrides ``stride``:

    * ``last_step_only``: only the final timestep of the (possibly restricted) range.
    * ``exact_step``: only that one timestep.
    * ``stride``: every timestep whose number divides by it.

    ``min_step`` and ``max_step`` restrict all three to a part of the run, e.g. to leave
    out the equilibration at the start of it.

    .. note::
        Nothing is written until the first geometry is found, so a selection which
        matches no timestep at all (asking for a timestep which is not in the file, for
        instance) leaves an existing output file alone rather than emptying it.

    :param history_path: Path to the HISTORY file to read.
    :param output_path: Path of the .xyz file to write the geometries to. It is
        overwritten if it exists.
    :param stride: Write every timestep whose number is a multiple of this, defaults to 1
        (every timestep in the file).
    :param min_step: The first timestep which may be written, defaults to 0 (the start of
        the run).
    :param max_step: The last timestep which may be written, defaults to None (the end of
        the run). Reading stops here, so this also cuts short the reading of a long
        HISTORY file.
    :param exact_step: Write only this timestep, defaults to None (use the stride).
    :param last_step_only: Write only the last timestep of the file (or of the range
        ``min_step`` to ``max_step``), defaults to False.
    :raises FileNotFoundError: If the HISTORY file does not exist.
    :return: What was written, see :class:`SubsampledTrajectory`.
    """

    history_path = Path(history_path)
    output_path = Path(output_path)

    if not history_path.is_file():
        raise FileNotFoundError(f"{history_path} is not a file.")

    stride = max(int(stride), 1)

    result = SubsampledTrajectory(history_path=history_path, output_path=None)

    def wanted(timestep: int) -> bool:
        """Whether a timestep is one of the ones which were asked for. The final timestep
        of a ``last_step_only`` extraction is not known until the end of the file, so it
        is dealt with separately."""
        if timestep < min_step:
            return False
        if max_step is not None and timestep > max_step:
            return False
        if exact_step is not None:
            return timestep == exact_step
        return timestep % stride == 0

    # the output file is only opened once there is something to write to it, so that a
    # selection which matches nothing does not empty an existing file
    out_f = None
    # the lines of the last timestep which is in range, kept unparsed for last_step_only
    last_frame = None

    try:

        with open(history_path, "r") as f:

            for timestep, natoms, frame_lines in _iter_history_frames(f):

                result.nframes_read += 1

                # timesteps are written to a HISTORY file in order, so there is nothing
                # left to read once the end of the requested range is passed
                if max_step is not None and timestep > max_step:
                    break

                if last_step_only:
                    if timestep >= min_step:
                        last_frame = (timestep, natoms, frame_lines)
                    continue

                if not wanted(timestep):
                    continue

                geometry = _parse_geometry(frame_lines, natoms)
                # a geometry with a different number of atoms is not part of the same
                # trajectory, so writing it would give an .xyz file of two molecules
                if geometry is None or (result.natoms and natoms != result.natoms):
                    result.nframes_skipped += 1
                    continue

                names, coordinates = geometry

                if out_f is None:
                    out_f = open(output_path, "w")
                    result.output_path = output_path
                    result.natoms = natoms
                    result.atom_names = names
                    result.first_timestep = timestep

                out_f.write(_geometry_str(names, coordinates, timestep))
                result.ngeometries += 1
                result.last_timestep = timestep

                # there is only ever one timestep with this number
                if exact_step is not None:
                    break

        if last_step_only and last_frame is not None:

            timestep, natoms, frame_lines = last_frame
            geometry = _parse_geometry(frame_lines, natoms)

            if geometry is None:
                result.nframes_skipped += 1
            else:
                names, coordinates = geometry
                out_f = open(output_path, "w")
                out_f.write(_geometry_str(names, coordinates, timestep))
                result.output_path = output_path
                result.natoms = natoms
                result.atom_names = names
                result.ngeometries = 1
                result.first_timestep = timestep
                result.last_timestep = timestep

    finally:
        if out_f is not None:
            out_f.close()

    return result
