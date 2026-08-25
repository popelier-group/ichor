from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from ichor.core.analysis import subsample_history
from ichor.core.files import Trajectory

# a water-like set of atoms, which is all a HISTORY file needs to be readable
ATOM_NAMES = ["O", "H", "H"]


def _frame(timestep: int, offset: float, binary: bool = False) -> str:
    """One timestep of a HISTORY file, whose coordinates are the atom index plus an
    offset, so that a geometry can be told apart from the others by its coordinates.

    :param timestep: The number of the timestep.
    :param offset: Added to every coordinate of the timestep.
    :param binary: Whether to write a null byte into the timestep, as DL_POLY
        occasionally does, which makes it unreadable.
    """

    # timestep ntimestep natoms keytrj imcon timestep_length time
    lines = [f"timestep {timestep} {len(ATOM_NAMES)} 0 1 0.001 {timestep * 0.001}\n"]
    lines += ["50.0 0.0 0.0\n", "0.0 50.0 0.0\n", "0.0 0.0 50.0\n"]

    for i, name in enumerate(ATOM_NAMES):
        lines.append(f"{name}{' ' * 7}{i + 1}   15.999   -0.4\n")
        coordinate = i + offset
        lines.append(f"{coordinate:16.8f}{coordinate:16.8f}{coordinate:16.8f}\n")

    if binary:
        lines[-1] = lines[-1].replace(" ", "\x00", 1)

    return "".join(lines)


def _write_history(
    path: Path, timesteps: Sequence[int], binary_timesteps: Sequence[int] = ()
) -> Path:
    """Writes a HISTORY file holding the given timesteps.

    :param path: Where to write the file.
    :param timesteps: The numbers of the timesteps the file holds.
    :param binary_timesteps: Which of those timesteps have binary written into them.
    """

    with open(path, "w") as f:
        f.write("test system\n")
        f.write(f"0 1 {len(ATOM_NAMES)} {len(timesteps)}\n")
        for i, timestep in enumerate(timesteps):
            f.write(_frame(timestep, float(i), binary=timestep in binary_timesteps))

    return path


def _timesteps_in(xyz_path: Path) -> List[int]:
    """The timesteps written on the comment lines of an extracted trajectory."""

    timesteps = []
    with open(xyz_path, "r") as f:
        for line in f:
            if line.startswith("timestep:"):
                timesteps.append(int(line.split(":")[1]))

    return timesteps


def _extract(
    tmp_path: Path,
    timesteps: Sequence[int],
    binary_timesteps: Sequence[int] = (),
    **kwargs,
) -> Tuple[Path, Optional[List[int]]]:
    """Writes a HISTORY file, extracts geometries from it, and returns the output path
    and the timesteps which ended up in it (None if nothing was written)."""

    history_path = _write_history(
        tmp_path / "HISTORY", timesteps, binary_timesteps=binary_timesteps
    )
    output_path = tmp_path / "sub_history.xyz"
    extracted = subsample_history(history_path, output_path, **kwargs)

    if not extracted.ngeometries:
        return output_path, None

    assert extracted.output_path == output_path
    assert extracted.natoms == len(ATOM_NAMES)
    assert extracted.atom_names == ATOM_NAMES

    written_timesteps = _timesteps_in(output_path)
    assert len(written_timesteps) == extracted.ngeometries
    assert written_timesteps[0] == extracted.first_timestep
    assert written_timesteps[-1] == extracted.last_timestep

    return output_path, written_timesteps


def test_every_timestep_is_extracted_by_default(tmp_path):
    """A stride of 1 writes out the whole trajectory."""

    _, timesteps = _extract(tmp_path, [0, 10, 20, 30])

    assert timesteps == [0, 10, 20, 30]


def test_stride_selects_timesteps_divisible_by_it(tmp_path):
    """The stride is applied to the timestep numbers, not to their position in the
    file, so that the geometries can be traced back to the run."""

    _, timesteps = _extract(tmp_path, list(range(0, 100, 10)), stride=25)

    assert timesteps == [0, 50]


def test_extracted_geometries_can_be_read_back_as_a_trajectory(tmp_path):
    """What is written is an .xyz file which ichor can read in again."""

    output_path, timesteps = _extract(tmp_path, [0, 10, 20], stride=10)
    trajectory = Trajectory(output_path)

    assert len(trajectory) == 3
    assert list(trajectory[0].names) == ["O1", "H2", "H3"]
    # the coordinates of the second geometry are its atom index plus its position in the
    # HISTORY file, which is what _frame writes
    assert list(trajectory[1][0].coordinates) == [1.0, 1.0, 1.0]


def test_first_and_last_timestep_restrict_the_range(tmp_path):
    """The equilibration at the start (and anything after the end) of a run is left
    out."""

    _, timesteps = _extract(
        tmp_path, list(range(0, 100, 10)), stride=10, min_step=20, max_step=60
    )

    assert timesteps == [20, 30, 40, 50, 60]


def test_exact_step_extracts_one_timestep(tmp_path):
    """A single timestep is written out on its own, whatever the stride is."""

    _, timesteps = _extract(tmp_path, list(range(0, 100, 10)), stride=50, exact_step=30)

    assert timesteps == [30]


def test_last_step_only_extracts_the_final_geometry(tmp_path):
    """The final geometry of a run is found without holding the trajectory in memory."""

    _, timesteps = _extract(tmp_path, [0, 10, 20, 30], last_step_only=True)

    assert timesteps == [30]


def test_last_step_only_respects_the_end_of_the_range(tmp_path):
    """The 'final' geometry of a restricted range is the last one in that range."""

    _, timesteps = _extract(tmp_path, [0, 10, 20, 30], last_step_only=True, max_step=20)

    assert timesteps == [20]


def test_timesteps_containing_binary_are_skipped(tmp_path):
    """DL_POLY occasionally writes binary into a HISTORY file, which corrupts a timestep
    but should not stop the rest of the trajectory being extracted."""

    history_path = _write_history(
        tmp_path / "HISTORY", [0, 10, 20, 30], binary_timesteps=[20]
    )
    extracted = subsample_history(history_path, tmp_path / "sub_history.xyz", stride=10)

    assert extracted.ngeometries == 3
    assert _timesteps_in(extracted.output_path) == [0, 10, 30]


def test_truncated_final_timestep_is_skipped(tmp_path):
    """A run which is still going has a half written timestep at the end of its HISTORY
    file, which is not a geometry."""

    history_path = _write_history(tmp_path / "HISTORY", [0, 10])
    with open(history_path, "a") as f:
        # everything but the last line of the timestep, i.e. one atom short
        f.write("".join(_frame(20, 2.0).splitlines(keepends=True)[:-1]))

    extracted = subsample_history(history_path, tmp_path / "sub_history.xyz", stride=10)

    assert _timesteps_in(extracted.output_path) == [0, 10]


def test_nothing_is_written_when_no_timestep_matches(tmp_path):
    """A selection which matches nothing leaves an existing output file alone, rather
    than emptying it."""

    output_path = tmp_path / "sub_history.xyz"
    output_path.write_text("existing geometries\n")

    history_path = _write_history(tmp_path / "HISTORY", [0, 10, 20])
    extracted = subsample_history(history_path, output_path, exact_step=15)

    assert extracted.ngeometries == 0
    assert extracted.output_path is None
    assert output_path.read_text() == "existing geometries\n"


def test_missing_history_file_raises(tmp_path):
    """A HISTORY file which is not there is an error rather than an empty trajectory."""

    try:
        subsample_history(tmp_path / "HISTORY", tmp_path / "sub_history.xyz")
    except FileNotFoundError:
        return

    raise AssertionError("a missing HISTORY file did not raise FileNotFoundError")
