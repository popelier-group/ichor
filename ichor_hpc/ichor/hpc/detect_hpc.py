"""Reading a cluster's queue settings out of SLURM, so that the ``hpc`` block of the
ichor config does not have to be written by hand.

The three settings under ``hpc`` all describe the queue rather than ichor: which
partitions exist and how many cores their nodes have, how much memory a core brings,
and how long a job may run. SLURM knows all of them, and ``sinfo`` will say so, so a
new cluster does not need someone to look them up and transcribe them.

Only SLURM is supported. The equivalent SGE commands vary far more between sites, and
guessing wrong there is worse than writing the block out by hand.
"""

import platform
import re
import shutil
import subprocess

from typing import List, NamedTuple, Optional

# sinfo should answer instantly; a hang means the queue is not healthy, and waiting
# on it is worse than telling the user to write the block themselves
SINFO_TIMEOUT_SECONDS = 30

# one line per partition, which every version of sinfo since well before SLURM 20
# understands. %P marks the default partition with a trailing *
SINFO_FORMAT = "%P|%c|%m|%l"

# what SLURM calls a partition with no time limit, and what that becomes in the
# config, where it means "write no limit and let the partition decide"
UNLIMITED_TIME_LIMITS = {"infinite", "unlimited", "none"}
NO_WALLTIME = "none"

# how much memory to assume a core brings if SLURM will not say
FALLBACK_MEMORY_PER_CORE_GB = 4


class DetectionUnavailable(Exception):
    """The cluster's settings could not be read, so there is nothing to write."""


class Partition(NamedTuple):
    """One SLURM partition, as much of it as the config cares about."""

    name: str
    is_default: bool
    cores_per_node: int
    memory_mb_per_node: Optional[int]
    time_limit: str

    @property
    def memory_per_core_gb(self) -> Optional[float]:
        """Returns the memory one core of this partition brings, in GB, worked out
        from the memory and cores of a node. None when SLURM did not report the
        memory, which some configurations do not.
        """

        if not self.memory_mb_per_node or not self.cores_per_node:
            return None

        return self.memory_mb_per_node / self.cores_per_node / 1024


def sinfo_is_available() -> bool:
    """Whether the SLURM tool that reports the partitions can be run here.

    :return: True if ``sinfo`` is on the PATH.
    """

    return shutil.which("sinfo") is not None


def run_sinfo() -> str:
    """Asks SLURM to describe every partition on this cluster.

    :raises DetectionUnavailable: If sinfo is missing, fails, or does not answer.
    :return: The raw output of sinfo, one partition per line.
    """

    if not sinfo_is_available():
        raise DetectionUnavailable(
            "sinfo was not found, so the queue settings cannot be read. Detection "
            "only works on SLURM, on a node where its tools are installed (usually "
            "a login node). Write the hpc block by hand instead."
        )

    try:
        result = subprocess.run(
            ["sinfo", "-h", "-o", SINFO_FORMAT],
            capture_output=True,
            text=True,
            timeout=SINFO_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise DetectionUnavailable(f"sinfo could not be run: {error}") from error

    if result.returncode != 0:
        raise DetectionUnavailable(
            f"sinfo exited with {result.returncode}: {result.stderr.strip()}"
        )

    return result.stdout


def _first_number(value: str) -> Optional[int]:
    """Reads the leading number out of a sinfo field.

    Counts come with markers that are not part of the number: cores are reported as
    ``64+`` when the nodes of a partition differ, and memory can carry a suffix.

    :param value: The field as sinfo wrote it.
    :return: The number in it, or None if there is not one.
    """

    match = re.match(r"\s*(\d+)", value)

    return int(match.group(1)) if match else None


def parse_sinfo(stdout: str) -> List[Partition]:
    """Turns sinfo output into the partitions of this cluster.

    sinfo writes a line per partition and node state, so a partition appears more
    than once when its nodes are not all in the same state. They are folded into one
    entry taking the largest node, as that is what decides the biggest job the
    partition can take.

    :param stdout: The raw output of :func:`run_sinfo`.
    :return: The partitions, in the order sinfo reported them.
    """

    partitions = {}

    for line in stdout.splitlines():
        fields = line.split("|")

        if len(fields) != 4:
            continue

        raw_name, raw_cores, raw_memory, time_limit = (f.strip() for f in fields)

        if not raw_name:
            continue

        # sinfo marks the default partition by appending a * to its name
        is_default = raw_name.endswith("*")
        name = raw_name.rstrip("*")
        cores = _first_number(raw_cores)

        if not cores:
            continue

        memory = _first_number(raw_memory)
        existing = partitions.get(name)

        if existing is None or cores > existing.cores_per_node:
            partitions[name] = Partition(
                name=name,
                is_default=is_default or (existing.is_default if existing else False),
                cores_per_node=cores,
                memory_mb_per_node=memory,
                time_limit=time_limit,
            )

    return list(partitions.values())


def detect_partitions() -> List[Partition]:
    """Returns the partitions of the cluster ichor is running on.

    :raises DetectionUnavailable: If SLURM reported no usable partitions.
    :return: The partitions.
    """

    partitions = parse_sinfo(run_sinfo())

    if not partitions:
        raise DetectionUnavailable(
            "sinfo reported no partitions, so there is nothing to write into the "
            "config. Write the hpc block by hand instead."
        )

    return partitions


def default_partition(partitions: List[Partition]) -> Partition:
    """Returns the partition a job goes to when it does not name one.

    That is the one the generated config is built around, as it is the one a site
    means jobs to use. If SLURM marks none as default, the one with the most cores
    is used, because it can take the widest range of jobs.

    :param partitions: The partitions of this cluster.
    :return: The partition to build the config around.
    """

    for partition in partitions:
        if partition.is_default:
            return partition

    return max(partitions, key=lambda partition: partition.cores_per_node)


def walltime_for_config(time_limit: str) -> str:
    """Turns a partition's time limit into what ``hpc.max_walltime`` should be.

    :param time_limit: The limit as sinfo reported it.
    :return: The value to write, which is ``none`` for a partition with no limit.
    """

    if time_limit.strip().lower() in UNLIMITED_TIME_LIMITS:
        return NO_WALLTIME

    return time_limit.strip()


def suggested_machine_key(hostname: Optional[str] = None) -> str:
    """Suggests the key to file this cluster's settings under.

    ichor picks a machine block by looking for a key that appears in the hostname, and
    it does that on compute nodes as well as on the login node. Those rarely share a
    full hostname but usually share a domain, so the domain is preferred over the host
    part, which normally carries a number that only one node has.

    :param hostname: The hostname to derive a key from, defaults to this machine's.
    :return: A key to suggest, which the user should still check against a compute node.
    """

    hostname = (hostname or platform.node()).strip().lower()
    labels = [label for label in hostname.split(".") if label]

    if not labels:
        return "mycluster"

    # a domain label is shared by every node of the cluster, unlike the host part
    if len(labels) > 1:
        return labels[1]

    # no domain, so fall back to the host part with any trailing node number removed
    return re.sub(r"[-_]?\d+$", "", labels[0]) or labels[0]


def detected_config_text(partitions: List[Partition], machine_key: str) -> str:
    """Builds a config file for this cluster out of what SLURM reported.

    Only the ``hpc`` block can be detected. The ``software`` block is where the
    programs are and which modules load them, which SLURM knows nothing about, so it
    is written out as a skeleton to be filled in.

    The default partition is given the whole range of core counts, rather than the
    partitions being split between ranges. A split would be guessing at which
    partition a job of a given size belongs in, and getting that wrong sends jobs
    somewhere the site did not intend; the other partitions are listed as comments so
    that the choice is there to make by hand.

    :param partitions: The partitions of this cluster.
    :param machine_key: The key to file the settings under.
    :return: The text of a config file.
    """

    chosen = default_partition(partitions)
    memory_per_core = chosen.memory_per_core_gb

    others = [
        f"    #   {partition.name}: {partition.cores_per_node} cores per node, "
        f"time limit {partition.time_limit}"
        for partition in partitions
        if partition.name != chosen.name
    ]
    other_partitions = (
        "\n    # The other partitions on this cluster, if you would rather send "
        "jobs of\n    # some sizes to one of them:\n" + "\n".join(others) + "\n"
        if others
        else ""
    )

    if memory_per_core is None:
        memory_line = (
            f"    # sinfo did not report the memory of {chosen.name}, so this is a "
            "guess.\n"
            "    # Set it to what a core actually brings, or jobs may ask for more "
            "memory\n    # than they are given and be killed on the node\n"
            f"    memory_per_core_gb: {FALLBACK_MEMORY_PER_CORE_GB}"
        )
    else:
        memory_line = (
            f"    # detected: {chosen.memory_mb_per_node} MB across "
            f"{chosen.cores_per_node} cores on a {chosen.name} node\n"
            f"    memory_per_core_gb: {round(memory_per_core, 1)}"
        )

    return f"""# ichor config, written by `ichor-config-init --detect`.
#
# The hpc block below was read from this cluster with `sinfo`. The software block was
# not, and cannot be: where each program lives and which module loads it is something
# only you know. Fill in the ones you use and delete the rest.
#
# This machine's hostname is {platform.node()}.
# ichor picks the block below by looking for its name in the hostname, and it does
# that on compute nodes too, whose names differ from this one. Check that the key
# still matches there, and shorten it if it does not.

{machine_key}:

  hpc:

    # detected: the default partition is {chosen.name}, whose nodes have
    # {chosen.cores_per_node} cores. Each key is a partition and each value the range
    # of core counts to use it for; every core count you submit with has to fall in
    # one of the ranges, including one core jobs
    parallel_environments:
      {chosen.name}: [1, {chosen.cores_per_node}]
{other_partitions}
{memory_line}

    # detected: the time limit of the {chosen.name} partition. SLURM rejects a job
    # asking for longer than this. Set to "none" to leave the limit out and let the
    # partition decide
    max_walltime: "{walltime_for_config(chosen.time_limit)}"

  software:

    # None of this can be detected. Set the programs you actually use, and delete
    # the rest. `module avail` lists what this cluster has.

    gaussian:
      executable_path: "g16"
      modules: []

    aimall:
      executable_path: "~/AIMAll/aimqb.ish"
      modules: []

    # Only needed for the ASE optimisation and metadynamics jobs, which run in their
    # own conda environment. Create it with `conda env create -f environment.yml`
    # from the ichor repository, then point these at it
    # python:
    #   env_name: "ichor_ase"
    #   python_path: "~/.conda/envs/ichor_ase/bin/python"
    #   modules: []
"""
