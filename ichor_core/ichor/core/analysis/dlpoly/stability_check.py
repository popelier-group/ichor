"""Stability analysis of DL_FFLUX (DL_POLY) simulations.

A DL_FFLUX simulation started from a poorly described part of configuration space tends
to fail by breaking a bond, either by the two atoms flying apart ("explosion") or by them
collapsing onto each other ("implosion"). This module detects such events by comparing
every bonded distance in a ``HISTORY`` trajectory against the corresponding distance in a
reference (usually optimised) geometry.

The ``HISTORY`` files of a robustness check are typically far too large to be held in
memory, so the trajectories are streamed rather than read in with
:class:`ichor.core.files.DlPolyHistory`.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Sequence, Tuple, Union

import numpy as np
from ichor.core.calculators import default_connectivity_calculator
from ichor.core.files import GJF, XYZ

__all__ = ["DlpolyStabilityCheck", "RunStability"]

EXPLOSION = "EXPLOSION"
IMPLOSION = "IMPLOSION"
STABLE = "STABLE"


@dataclass
class RunStability:
    """The outcome of the stability analysis of a single DL_FFLUX run.

    :param run: Name of the run (the name of the directory containing the HISTORY file).
    :param last_timestep: The last timestep present in the HISTORY file.
    :param stable_timesteps: The number of timesteps for which the geometry stayed intact,
        i.e. the timestep at which the first bond broke, or ``last_timestep`` if no bond
        ever broke.
    :param status: One of ``"STABLE"``, ``"EXPLOSION"`` or ``"IMPLOSION"``.
    :param recovered: True if a bond broke during the simulation but the final geometry is
        intact again (the run "recovered" from the event).
    :param bond: The name of the first bond that broke, e.g. ``"C1-H2"``, or None.
    :param bond_length: The length of that bond at the timestep at which it broke, or None.
    :param reference_bond_length: The length of that bond in the reference geometry, or None.
    """

    run: str
    last_timestep: int
    stable_timesteps: int
    status: str = STABLE
    recovered: bool = False
    bond: Optional[str] = None
    bond_length: Optional[float] = None
    reference_bond_length: Optional[float] = None

    @property
    def crashed(self) -> bool:
        """Whether a bond broke at any point during the run."""
        return self.status != STABLE


class DlpolyStabilityCheck:
    """Checks a set of DL_FFLUX runs for broken bonds (explosions / implosions).

    Each run is scanned in two stages. First the trajectory is scanned every ``stride``
    timesteps (plus the very last timestep) to find out roughly where, if anywhere, the
    geometry falls apart. Only if something is found is the trajectory scanned again, this
    time timestep by timestep, over the (at most ``stride`` long) window in which the
    breakage must have happened, so that the exact timestep can be reported. This keeps
    the cost of checking a stable, multi-million timestep run down to a single cheap pass.

    .. note::
        A bond which breaks and heals again entirely within one stride is not seen by the
        first pass, so the stride should be well below the length of the runs. Runs
        shorter than two strides are checked timestep by timestep instead, as they are
        cheap enough to do so.

    :param reference_geometry: Path to the reference geometry (``.xyz`` or ``.gjf``),
        usually the optimised geometry of the molecule. Its connectivity and bond lengths
        define what "intact" means, and its atom ordering must match the runs.
    :param run_directories: The directories containing the ``HISTORY`` files to check
        (e.g. the ``RUN*`` directories written by a robustness check). Directories which
        do not contain a HISTORY file are skipped.
    :param stride: How often (in timesteps) the trajectory is checked in the first pass,
        defaults to 1000.
    :param explosion_factor: A bond is considered exploded when it is longer than
        ``explosion_factor`` times its reference length, defaults to 1.35.
    :param implosion_factor: A bond is considered imploded when it is shorter than its
        reference length divided by ``implosion_factor``, defaults to 1.5.
    :param history_file_name: Name of the trajectory file inside each run directory,
        defaults to ``"HISTORY"``.

    Example usage:

    .. code-block:: python

        check = DlpolyStabilityCheck("opt.xyz", Path("robustness").glob("RUN*"))
        check.write_report("STABILITY-REPORT.txt", max_timesteps=2000000)
    """

    def __init__(
        self,
        reference_geometry: Union[str, Path],
        run_directories: Sequence[Union[str, Path]],
        stride: int = 1000,
        explosion_factor: float = 1.35,
        implosion_factor: float = 1.5,
        history_file_name: str = "HISTORY",
    ):

        reference_geometry = Path(reference_geometry)
        self.reference_geometry = reference_geometry
        self.run_directories = [Path(r) for r in run_directories]
        self.stride = max(int(stride), 1)
        self.explosion_factor = explosion_factor
        self.implosion_factor = implosion_factor
        self.history_file_name = history_file_name

        reference_file = (
            GJF(reference_geometry)
            if reference_geometry.suffix == ".gjf"
            else XYZ(reference_geometry)
        )
        self.reference_atoms = reference_file.atoms
        self.atom_names = list(self.reference_atoms.names)

        # indices of the bonded (and only the bonded) atom pairs, i < j, and the
        # corresponding reference bond lengths, so that a whole geometry can be checked
        # with a single vectorised operation
        connectivity = default_connectivity_calculator(self.reference_atoms)
        self._bonded_i, self._bonded_j = np.nonzero(np.triu(connectivity, k=1))
        reference_coordinates = self.reference_atoms.coordinates
        self._reference_bond_lengths = np.linalg.norm(
            reference_coordinates[self._bonded_i]
            - reference_coordinates[self._bonded_j],
            axis=1,
        )

        self.results: List[RunStability] = []
        self.analyse()

    @property
    def natoms(self) -> int:
        """The number of atoms in the reference geometry."""
        return len(self.atom_names)

    def bond_name(self, i: int, j: int) -> str:
        """Returns the name of the bond between atoms with indices ``i`` and ``j``,
        e.g. ``"C1-H2"``."""
        return f"{self.atom_names[i]}-{self.atom_names[j]}"

    def broken_bonds_in_geometry(
        self, coordinates: np.ndarray
    ) -> List[Tuple[int, int, float, str]]:
        """Finds the bonds of a geometry which are broken with respect to the reference.

        :param coordinates: A ``natoms x 3`` array of coordinates.
        :return: A list of ``(i, j, bond_length, status)`` tuples, one for each broken
            bond, where ``i`` and ``j`` are atom indices and ``status`` is either
            ``"EXPLOSION"`` or ``"IMPLOSION"``. Empty if the geometry is intact.
        """

        lengths = np.linalg.norm(
            coordinates[self._bonded_i] - coordinates[self._bonded_j], axis=1
        )
        exploded = lengths > self._reference_bond_lengths * self.explosion_factor
        imploded = lengths < self._reference_bond_lengths / self.implosion_factor

        broken = []
        for idx in np.nonzero(exploded | imploded)[0]:
            broken.append(
                (
                    int(self._bonded_i[idx]),
                    int(self._bonded_j[idx]),
                    float(lengths[idx]),
                    EXPLOSION if exploded[idx] else IMPLOSION,
                )
            )

        return broken

    def analyse(self) -> List[RunStability]:
        """Analyses every run directory and stores the outcome in ``self.results``.

        :return: The list of per-run results.
        """

        self.results = []
        for run_directory in self.run_directories:
            history_path = run_directory / self.history_file_name
            if not history_path.is_file():
                continue
            result = self.analyse_run(history_path, run_name=run_directory.name)
            if result is not None:
                self.results.append(result)

        return self.results

    def analyse_run(
        self, history_path: Union[str, Path], run_name: Optional[str] = None
    ) -> Optional[RunStability]:
        """Analyses a single HISTORY file.

        :param history_path: Path to the HISTORY file.
        :param run_name: Name to report the run under, defaults to the name of the
            directory containing the HISTORY file.
        :return: The stability of this run, or None if the HISTORY file contains no
            readable timesteps.
        """

        history_path = Path(history_path)
        run_name = run_name if run_name is not None else history_path.parent.name

        # first (cheap) pass: check every stride-th timestep and the final timestep
        first_broken_stride_timestep = None
        first_broken_stride_bonds = []
        last_clean_stride_timestep = 0
        last_timestep = None
        last_coordinates = None

        for timestep, coordinates in self._iter_history(
            history_path, stride=self.stride
        ):
            # the final timestep is always yielded, so it is not necessarily a stride one
            last_timestep, last_coordinates = timestep, coordinates
            if first_broken_stride_timestep is not None:
                continue
            if timestep % self.stride != 0:
                continue
            broken_bonds = self.broken_bonds_in_geometry(coordinates)
            if broken_bonds:
                first_broken_stride_timestep = timestep
                first_broken_stride_bonds = broken_bonds
            else:
                last_clean_stride_timestep = timestep

        if last_timestep is None:
            return None

        broken_at_end = bool(self.broken_bonds_in_geometry(last_coordinates))

        if first_broken_stride_timestep is None and not broken_at_end:

            # a run shorter than a couple of strides is hardly checked by the first pass
            # at all (a 500 timestep run checked with a stride of 1000 is only looked at
            # on its first and last timestep), so a bond that broke and healed again in
            # between would be missed. Such a run is short enough to just check in full,
            # i.e. from the timestep after the (always checked) first one to the end.
            if last_timestep < 2 * self.stride:
                crash_timestep, broken_bonds = self._find_first_broken_timestep(
                    history_path, (0, last_timestep)
                )
                if crash_timestep is not None:
                    return self._crashed_run_stability(
                        run_name, last_timestep, crash_timestep, broken_bonds, False
                    )

            return RunStability(
                run=run_name,
                last_timestep=last_timestep,
                stable_timesteps=last_timestep,
            )

        # second pass: the geometry broke somewhere after the last intact checked timestep
        # and at (or before) the first timestep at which it was seen broken, so scan that
        # window timestep by timestep to find out exactly when and which bond went first
        if first_broken_stride_timestep is not None:
            window = (last_clean_stride_timestep, first_broken_stride_timestep)
        else:
            window = (last_clean_stride_timestep, last_timestep)

        crash_timestep, broken_bonds = self._find_first_broken_timestep(
            history_path, window
        )

        # nothing found in the window means the geometry was already broken at its lower
        # end (i.e. at the very first timestep of the run) or the HISTORY file is
        # corrupted there, so fall back on what the first pass found
        if crash_timestep is None:
            if first_broken_stride_timestep is not None:
                crash_timestep = first_broken_stride_timestep
                broken_bonds = first_broken_stride_bonds
            else:
                crash_timestep = last_timestep
                broken_bonds = self.broken_bonds_in_geometry(last_coordinates)

        return self._crashed_run_stability(
            run_name, last_timestep, crash_timestep, broken_bonds, broken_at_end
        )

    def _crashed_run_stability(
        self,
        run_name: str,
        last_timestep: int,
        crash_timestep: int,
        broken_bonds: List[Tuple[int, int, float, str]],
        broken_at_end: bool,
    ) -> RunStability:
        """Builds the result of a run which broke a bond, reporting the first of the
        bonds that broke at ``crash_timestep``."""

        i, j, bond_length, status = broken_bonds[0]

        return RunStability(
            run=run_name,
            last_timestep=last_timestep,
            stable_timesteps=crash_timestep,
            status=status,
            # a run whose final geometry is intact again recovered from the event
            recovered=not broken_at_end,
            bond=self.bond_name(i, j),
            bond_length=bond_length,
            reference_bond_length=float(
                np.linalg.norm(
                    self.reference_atoms.coordinates[i]
                    - self.reference_atoms.coordinates[j]
                )
            ),
        )

    def _find_first_broken_timestep(
        self, history_path: Path, window: Tuple[int, int]
    ) -> Tuple[Optional[int], List[Tuple[int, int, float, str]]]:
        """Scans the timesteps in ``(low, high]`` and returns the first one at which a
        bond is broken, together with the bonds that are broken at it."""

        low, high = window
        for timestep, coordinates in self._iter_history(history_path):
            if timestep <= low:
                continue
            if timestep > high:
                break
            broken_bonds = self.broken_bonds_in_geometry(coordinates)
            if broken_bonds:
                return timestep, broken_bonds

        return None, []

    def _iter_history(
        self, history_path: Path, stride: int = 1
    ) -> Iterator[Tuple[int, np.ndarray]]:
        """Streams a HISTORY file, yielding ``(timestep, coordinates)``.

        Only the coordinates of the timesteps that are actually needed are parsed, i.e.
        every ``stride``-th timestep and (always) the final timestep of the file.
        Timesteps containing binary data, which DL_POLY occasionally writes into HISTORY
        files, are skipped, as are timesteps whose number of atoms does not match the
        reference geometry.

        :param history_path: Path to the HISTORY file.
        :param stride: Only yield timesteps whose number is a multiple of this,
            defaults to 1 (every timestep).
        """

        previous_lines = None
        previous_timestep = None

        with open(history_path, "r") as f:
            for timestep, frame_lines in self._iter_raw_frames(f):

                # the last timestep of the file matters regardless of the stride, but it
                # is only known to be the last one after the next timestep is read, so
                # timesteps are yielded one behind
                if previous_lines is not None:
                    if previous_timestep % stride == 0:
                        coordinates = self._parse_coordinates(previous_lines)
                        if coordinates is not None:
                            yield previous_timestep, coordinates
                previous_lines, previous_timestep = frame_lines, timestep

        if previous_lines is not None:
            coordinates = self._parse_coordinates(previous_lines)
            if coordinates is not None:
                yield previous_timestep, coordinates

    def _iter_raw_frames(self, f) -> Iterator[Tuple[int, List[str]]]:
        """Splits an open HISTORY file into ``(timestep, lines)``, without parsing the
        coordinates. The two header lines at the top of a HISTORY file are skipped
        implicitly, as everything before the first ``timestep`` record is ignored."""

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
                # a new timestep record before the current one is complete means the
                # current one is truncated, so resynchronise on the new record
                if line.split()[:1] == ["timestep"]:
                    break
                frame_lines.append(line)
                line = f.readline()

            if len(frame_lines) == nlines and natoms == self.natoms:
                yield timestep, frame_lines

    def _parse_coordinates(self, frame_lines: List[str]) -> Optional[np.ndarray]:
        """Parses the atomic coordinates out of the lines of a single timestep.
        Returns None if the timestep contains binary or otherwise unreadable data."""

        # DL_POLY sometimes writes binary into the HISTORY file, which corrupts a timestep
        if any("\x00" in line for line in frame_lines):
            return None

        # 3 unit cell lines, then blocks of (name, coordinates, [velocity], [force])
        lines_per_atom = (len(frame_lines) - 3) // self.natoms
        coordinates = np.empty((self.natoms, 3))
        for atom_index in range(self.natoms):
            coordinate_line = frame_lines[3 + atom_index * lines_per_atom + 1]
            try:
                coordinates[atom_index] = [
                    float(c) for c in coordinate_line.split()[:3]
                ]
            except ValueError:
                return None

        return coordinates

    def broken_bond_counts(self) -> Dict[str, Dict[str, int]]:
        """Counts, over all runs, how often each bond was the first one to break.

        :return: A dictionary of bond name to a dictionary containing the number of
            ``"EXPLOSION"`` and ``"IMPLOSION"`` events for that bond and their ``"total"``.
        """

        counts: Dict[str, Dict[str, int]] = {}
        for result in self.results:
            if not result.crashed:
                continue
            bond_counts = counts.setdefault(
                result.bond, {EXPLOSION: 0, IMPLOSION: 0, "total": 0}
            )
            bond_counts[result.status] += 1
            bond_counts["total"] += 1

        return counts

    def robustness(self, max_timesteps: Optional[int] = None) -> float:
        """The fraction of the requested simulation time over which the models kept the
        simulations intact, averaged over all runs. A robustness of 1.0 means that every
        run survived for the full simulation.

        :param max_timesteps: The number of timesteps each run was meant to last for. If
            None (default), the longest run in the set is used.
        """

        if not self.results:
            return 0.0

        max_timesteps = max_timesteps or max(r.last_timestep for r in self.results)
        if max_timesteps <= 0:
            return 0.0

        total = sum(min(r.stable_timesteps, max_timesteps) for r in self.results)

        return total / (len(self.results) * max_timesteps)

    def stability_times(self, timestep_length: float = 0.001) -> Dict[str, float]:
        """The time (in ps) for which the runs stayed intact.

        :param timestep_length: The length of one timestep in ps, defaults to 0.001.
        :return: A dictionary with the ``"min"``, ``"max"`` and ``"mean"`` stability
            times, in ps.
        """

        if not self.results:
            return {"min": 0.0, "max": 0.0, "mean": 0.0}

        # the first timestep in a HISTORY file is the starting geometry, so the simulated
        # time is one timestep shorter than the number of the timestep reached
        times = [max(r.stable_timesteps - 1, 0) * timestep_length for r in self.results]

        return {
            "min": min(times),
            "max": max(times),
            "mean": sum(times) / len(times),
        }

    def report(
        self,
        max_timesteps: Optional[int] = None,
        timestep_length: float = 0.001,
    ) -> str:
        """Builds a human readable stability report.

        The report contains one line per run (the timestep at which it broke, if it did,
        and which bond went first), a summary of which bonds break most often, and the
        overall robustness and stability times.

        :param max_timesteps: The number of timesteps each run was meant to last for,
            used for the robustness. If None (default), the longest run is used.
        :param timestep_length: The length of one timestep in ps, defaults to 0.001.
        :return: The report as a string.
        """

        lines = [
            f"{'RUN':>10} {'STEPS':>10} {'BOND':>12} {'BOND-LENGTH':>16}"
            f" {'REF-BOND-LENGTH':>18} {'STATUS':>20}"
        ]

        for result in self.results:
            if not result.crashed:
                lines.append(
                    f"{result.run:>10} {result.stable_timesteps:>10} {'NA':>12}"
                    f" {'NA':>16} {'NA':>18} {STABLE:>20}"
                )
            else:
                status = result.status + ("-RECOVERED" if result.recovered else "")
                lines.append(
                    f"{result.run:>10} {result.stable_timesteps:>10} {result.bond:>12}"
                    f" {result.bond_length:>16.3e}"
                    f" {result.reference_bond_length:>18.3e} {status:>20}"
                )

        lines.append("")
        lines.append(
            f"{'BROKEN-BOND':>12} {'CONTRIBUTION':>16} {'EXPLOSIONS':>12} {'IMPLOSIONS':>12}"
        )

        counts = self.broken_bond_counts()
        total_broken = sum(c["total"] for c in counts.values())
        if not counts:
            lines.append(f"{'NA':>12} {'NA':>16} {'NA':>12} {'NA':>12}")
        for bond, bond_counts in sorted(
            counts.items(), key=lambda item: item[1]["total"], reverse=True
        ):
            contribution = 100.0 * bond_counts["total"] / total_broken
            lines.append(
                f"{bond:>12} {contribution:>15.1f}% {bond_counts[EXPLOSION]:>12}"
                f" {bond_counts[IMPLOSION]:>12}"
            )

        times = self.stability_times(timestep_length)
        nstable = sum(1 for r in self.results if not r.crashed)
        lines.append("")
        lines.append(f"{'Runs':>15} {len(self.results):>12}")
        lines.append(f"{'Stable runs':>15} {nstable:>12}")
        lines.append(f"{'Robustness':>15} {self.robustness(max_timesteps):>12.4f}")
        lines.append(f"{'Min.Stab(ps)':>15} {times['min']:>12.4f}")
        lines.append(f"{'Max.Stab(ps)':>15} {times['max']:>12.4f}")
        lines.append(f"{'Mean.Stab(ps)':>15} {times['mean']:>12.4f}")

        return "\n".join(lines) + "\n"

    def write_report(
        self,
        path: Union[str, Path] = "STABILITY-REPORT.txt",
        max_timesteps: Optional[int] = None,
        timestep_length: float = 0.001,
    ) -> Path:
        """Writes the report of :meth:`report` to a file.

        :param path: Path of the report file, defaults to ``"STABILITY-REPORT.txt"``.
        :param max_timesteps: The number of timesteps each run was meant to last for,
            used for the robustness. If None (default), the longest run is used.
        :param timestep_length: The length of one timestep in ps, defaults to 0.001.
        :return: The path the report was written to.
        """

        path = Path(path)

        with open(path, "w") as f:
            f.write(self.report(max_timesteps, timestep_length))

        return path
