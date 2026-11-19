"""Changing the ``hpc`` block of the ichor config from inside ichor.

The ``hpc`` block says which partitions jobs are sent to, how long they may run for
and how much memory a core brings. These are the settings most likely to need
changing between runs (moving small jobs onto a partition with a shorter queue, or
asking for longer to finish a slow calculation), so the menu system can change them
rather than the config having to be edited by hand.

The config is written back with ``ruamel.yaml``, which keeps the comments, key order
and quoting of the file as it was, so that a file a user has annotated is not
rewritten into something they no longer recognise. The previous version is kept next
to it as a ``.bak`` file.
"""

import os
import re
import shutil

from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterator, List, Mapping, MutableMapping, Tuple, Union

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarstring import DoubleQuotedScalarString

# what hpc.max_walltime is set to in order to leave the time limit off entirely, the
# same as ichor.hpc.global_variables.NO_WALLTIME (not imported from there, as that
# module reads the config when it is imported)
NO_WALLTIME = "none"

# the forms SLURM accepts for a time limit: minutes, minutes:seconds,
# hours:minutes:seconds, days-hours, days-hours:minutes and days-hours:minutes:seconds
WALLTIME_PATTERN = re.compile(r"^(\d+-\d+(:\d+){0,2}|\d+(:\d+){0,2})$")

CoreRange = Tuple[int, int]


class HpcSettingsError(ValueError):
    """A change to the ``hpc`` block that cannot be made as asked."""


def normalise_walltime(value: str) -> str:
    """Checks that a time limit is written in a form the batch system accepts.

    :param value: The time limit, e.g. ``3-0``, ``24:00:00`` or ``none``.
    :return: The time limit with surrounding whitespace removed, and ``none`` in
        lower case.
    :raises HpcSettingsError: If it is not in a form SLURM accepts.
    """

    value = str(value).strip()

    if value.lower() == NO_WALLTIME:
        return NO_WALLTIME

    if not WALLTIME_PATTERN.match(value):
        raise HpcSettingsError(
            f"{value!r} is not a time limit SLURM accepts. Use days-hours (3-0), "
            "days-hours:minutes:seconds (1-12:00:00), hours:minutes:seconds "
            f"(24:00:00), minutes (90), or {NO_WALLTIME!r} to leave the limit to the "
            "partition."
        )

    return value


def check_core_range(low: int, high: int) -> CoreRange:
    """Checks that a range of core counts makes sense on its own.

    :raises HpcSettingsError: If either end is below one or the range is backwards.
    """

    low, high = int(low), int(high)

    if low < 1:
        raise HpcSettingsError("A partition's smallest core count must be at least 1.")
    if high < low:
        raise HpcSettingsError(
            f"The largest core count ({high}) is smaller than the smallest ({low})."
        )

    return low, high


def ranges_overlap(first: CoreRange, second: CoreRange) -> bool:
    """Whether two core ranges have any core count in common."""

    return first[0] <= second[1] and second[0] <= first[1]


def remaining_range(existing: CoreRange, taken: CoreRange) -> List[CoreRange]:
    """What is left of a core range once another range has been taken out of it.

    :return: No ranges when ``taken`` covers all of ``existing``, one when it covers
        one end, and two when it falls in the middle and splits it.
    """

    pieces = []

    if existing[0] < taken[0]:
        pieces.append((existing[0], min(existing[1], taken[0] - 1)))
    if existing[1] > taken[1]:
        pieces.append((max(existing[0], taken[1] + 1), existing[1]))

    return pieces


def overlapping_partitions(
    ranges: Mapping[str, CoreRange], name: str, new_range: CoreRange
) -> Dict[str, CoreRange]:
    """The partitions, other than ``name`` itself, whose range shares core counts with
    ``new_range``."""

    return {
        other: tuple(other_range)
        for other, other_range in ranges.items()
        if other != name and ranges_overlap(tuple(other_range), new_range)
    }


def range_problems(ranges: Mapping[str, CoreRange]) -> List[str]:
    """Things wrong with a set of partition ranges that would send jobs somewhere
    other than intended, worded for the user.

    Overlapping ranges are not an error to the batch system, but a core count that two
    partitions cover goes to whichever is listed first, which is rarely what was meant.
    A gap means a job with that many cores cannot be submitted at all.
    """

    problems = []
    items = [(name, tuple(core_range)) for name, core_range in ranges.items()]

    for i, (name, core_range) in enumerate(items):
        for other, other_range in items[i + 1 :]:
            if ranges_overlap(core_range, other_range):
                low = max(core_range[0], other_range[0])
                high = min(core_range[1], other_range[1])
                problems.append(
                    f"{name} and {other} both cover {low}-{high} cores; jobs of that "
                    f"size go to {name}, as it is listed first."
                )

    for low, high in uncovered_core_counts(ranges):
        cores = f"{low} core" if low == high else f"{low}-{high} cores"
        problems.append(
            f"No partition covers {cores}, so jobs of that size cannot be submitted."
        )

    return problems


def uncovered_core_counts(ranges: Mapping[str, CoreRange]) -> List[CoreRange]:
    """The core counts from one up to the largest configured that no partition
    covers."""

    if not ranges:
        return []

    covered = sorted(tuple(core_range) for core_range in ranges.values())
    gaps = []
    next_uncovered = 1

    for low, high in covered:
        if low > next_uncovered:
            gaps.append((next_uncovered, low - 1))
        next_uncovered = max(next_uncovered, high + 1)

    return gaps


def _flow_range(low: int, high: int) -> CommentedSeq:
    """A ``[low, high]`` list written on one line, as the rest of the config has them."""

    seq = CommentedSeq([low, high])
    seq.fa.set_flow_style()
    return seq


def _replace_key(mapping: MutableMapping, old: str, new: str):
    """Renames a key in place, keeping its position (and so the order partitions are
    tried in, which decides who gets an overlapping core count)."""

    if isinstance(mapping, CommentedMap):
        position = list(mapping.keys()).index(old)
        value = mapping.pop(old)
        mapping.insert(position, new, value)
        return

    items = [(new if key == old else key, value) for key, value in mapping.items()]
    mapping.clear()
    mapping.update(items)


def partitions(hpc: Mapping) -> Dict[str, CoreRange]:
    """The partitions in an ``hpc`` block, as ``{name: (low, high)}``."""

    environments = hpc.get("parallel_environments") or {}
    return {name: (int(r[0]), int(r[1])) for name, r in environments.items()}


def set_partition(hpc: MutableMapping, name: str, low: int, high: int):
    """Adds a partition, or changes the core counts an existing one is used for.

    Other partitions are left alone even if the new range overlaps them; see
    :func:`trim_partition` for taking the overlap out of them.
    """

    name = str(name).strip()
    if not name:
        raise HpcSettingsError("A partition needs a name.")
    low, high = check_core_range(low, high)

    environments = hpc.get("parallel_environments")
    if environments is None:
        environments = CommentedMap()
        hpc["parallel_environments"] = environments

    environments[name] = _flow_range(low, high)


def trim_partition(hpc: MutableMapping, name: str, taken: CoreRange):
    """Takes the core counts in ``taken`` out of a partition's range, so that another
    partition can have them.

    :raises HpcSettingsError: If nothing of the partition would be left, or if it would
        be split in two, as one partition can only have one range.
    """

    existing = partitions(hpc)[name]
    pieces = remaining_range(existing, taken)

    if not pieces:
        raise HpcSettingsError(
            f"{name} [{existing[0]}, {existing[1]}] would be left with no core counts. "
            "Remove it, or rename it, instead."
        )
    if len(pieces) > 1:
        raise HpcSettingsError(
            f"{name} [{existing[0]}, {existing[1]}] would be split in two around "
            f"[{taken[0]}, {taken[1]}], and a partition can only have one range. "
            f"Change {name}'s range first."
        )

    hpc["parallel_environments"][name] = _flow_range(*pieces[0])


def rename_partition(hpc: MutableMapping, old: str, new: str):
    """Renames a partition, e.g. ``multicore`` to ``multicore_small``, keeping its core
    range, its place in the order, and any memory given for it by name."""

    new = str(new).strip()
    if not new:
        raise HpcSettingsError("A partition needs a name.")

    environments = hpc.get("parallel_environments") or {}
    if old not in environments:
        raise HpcSettingsError(f"There is no partition called {old!r}.")
    if new == old:
        return
    if new in environments:
        raise HpcSettingsError(f"There is already a partition called {new!r}.")

    _replace_key(environments, old, new)

    memory = hpc.get("memory_per_core_gb")
    if isinstance(memory, MutableMapping) and old in memory:
        _replace_key(memory, old, new)


def remove_partition(hpc: MutableMapping, name: str):
    """Removes a partition, along with any memory given for it by name."""

    environments = hpc.get("parallel_environments") or {}
    if name not in environments:
        raise HpcSettingsError(f"There is no partition called {name!r}.")

    del environments[name]

    memory = hpc.get("memory_per_core_gb")
    if isinstance(memory, MutableMapping) and name in memory:
        del memory[name]


def set_max_walltime(hpc: MutableMapping, value: str):
    """Sets how long jobs may run for, see :func:`normalise_walltime`."""

    hpc["max_walltime"] = DoubleQuotedScalarString(normalise_walltime(value))


def _checked_memory(gb) -> Union[int, float]:
    """Checks an amount of memory per core, written as 8 rather than 8.0 when it is a
    whole number, as the config has them."""

    gb = float(gb)
    if gb <= 0:
        raise HpcSettingsError("Memory per core must be more than 0 GB.")

    return int(gb) if gb.is_integer() else gb


def set_memory_per_core_gb(
    hpc: MutableMapping, value: Union[float, Mapping[str, float]]
):
    """Sets how much memory a core brings, either one number for every partition or
    one per partition (keyed by partition name)."""

    if isinstance(value, Mapping):
        memory = CommentedMap()
        for name, gb in value.items():
            memory[name] = _checked_memory(gb)
        hpc["memory_per_core_gb"] = memory
    else:
        hpc["memory_per_core_gb"] = _checked_memory(value)


def set_partition_memory_per_core_gb(hpc: MutableMapping, name: str, gb: float):
    """Sets the memory a core brings on one partition, when memory is given per
    partition.

    :raises HpcSettingsError: If memory is given as one number for every partition,
        in which case there is nothing to set per partition.
    """

    memory = hpc.get("memory_per_core_gb")
    if not isinstance(memory, MutableMapping):
        raise HpcSettingsError(
            "Memory per core is one number for every partition, not one per partition."
        )

    memory[name] = _checked_memory(gb)


def _yaml() -> YAML:
    """A YAML reader/writer that leaves the parts of the file it is not asked to change
    as they were."""

    yaml = YAML()
    yaml.preserve_quotes = True
    return yaml


def backup_path(config_path: Path) -> Path:
    """Where the previous version of the config is kept after it is changed."""

    return config_path.with_name(config_path.name + ".bak")


@contextmanager
def edit_hpc_block(config_path: Path, machine: str) -> Iterator[MutableMapping]:
    """Reads the config, gives the ``hpc`` block of ``machine`` to be changed, and
    writes the config back if the block of code completes without raising.

    The file is read afresh each time, so changes made by hand while ichor is running
    are not overwritten with what ichor read when it started. The previous version is
    copied to a ``.bak`` file next to it, and the new one is written to a temporary
    file and moved into place, so that a failed write cannot leave half a config.

    :raises HpcSettingsError: If the config has no block for ``machine``.
    """

    # resolved so that a config which is a link to a file elsewhere has that file
    # changed, rather than the link being replaced with a copy
    config_path = Path(config_path).resolve()
    yaml = _yaml()

    with open(config_path, "r") as f:
        config = yaml.load(f)

    if not isinstance(config, MutableMapping) or machine not in config:
        raise HpcSettingsError(f"{config_path} has no block for {machine!r}.")

    machine_block = config[machine]
    if machine_block is None:
        machine_block = CommentedMap()
        config[machine] = machine_block

    hpc = machine_block.get("hpc")
    if hpc is None:
        hpc = CommentedMap()
        machine_block["hpc"] = hpc

    yield hpc

    shutil.copy2(config_path, backup_path(config_path))

    temporary = config_path.with_name(config_path.name + ".tmp")
    with open(temporary, "w", newline="\n") as f:
        yaml.dump(config, f)
    os.replace(temporary, config_path)
