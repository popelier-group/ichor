"""Tests for reading a cluster's queue settings out of SLURM.

The parsing is what matters here: sinfo output varies between sites and versions,
and a value read wrong ends up in a config file that looks right and produces jobs
the queue rejects.
"""

import pytest

import yaml

from ichor.hpc.detect_hpc import (
    default_partition,
    detected_config_text,
    parse_sinfo,
    Partition,
    suggested_machine_key,
    walltime_for_config,
)

# what `sinfo -h -o "%P|%c|%m|%l"` gives on a cluster with a few partitions. The *
# marks the default, and a partition appears once per node state
TYPICAL_SINFO = """\
compute*|64|256000|1-00:00:00
compute*|64|256000|1-00:00:00
serial|16|64000|7-00:00:00
gpu|32|512000|12:00:00
"""


def test_partitions_are_parsed():
    """The ordinary case."""

    partitions = parse_sinfo(TYPICAL_SINFO)

    assert [p.name for p in partitions] == ["compute", "serial", "gpu"]
    assert partitions[0].cores_per_node == 64
    assert partitions[0].memory_mb_per_node == 256000
    assert partitions[0].time_limit == "1-00:00:00"


def test_repeated_partitions_are_folded_together():
    """sinfo writes a line per partition and node state, so the same partition
    appears more than once when its nodes are not all up."""

    partitions = parse_sinfo(TYPICAL_SINFO)

    assert len([p for p in partitions if p.name == "compute"]) == 1


def test_the_largest_node_of_a_partition_is_taken():
    """A partition whose nodes differ should be sized by its biggest, as that is
    what decides the largest job it can take."""

    partitions = parse_sinfo("mixed|16|64000|1-00:00:00\nmixed|128|512000|1-00:00:00\n")

    assert partitions[0].cores_per_node == 128


def test_the_default_partition_is_recognised():
    """The * that sinfo appends is how the default is marked, and it must not end
    up in the partition name written to the config."""

    chosen = default_partition(parse_sinfo(TYPICAL_SINFO))

    assert chosen.name == "compute"
    assert chosen.is_default


def test_the_biggest_partition_is_used_when_none_is_default():
    """Not every cluster marks a default partition."""

    partitions = parse_sinfo("small|8|32000|1-00:00:00\nbig|64|256000|1-00:00:00\n")

    assert default_partition(partitions).name == "big"


def test_counts_with_a_plus_are_read():
    """sinfo writes `64+` when the nodes of a partition are not all the same, which
    is not an integer and used to be pointless to parse with int()."""

    partitions = parse_sinfo("compute*|64+|256000+|1-00:00:00\n")

    assert partitions[0].cores_per_node == 64
    assert partitions[0].memory_mb_per_node == 256000


def test_unparseable_lines_are_skipped():
    """sinfo can emit blank lines and headers depending on the version; one bad
    line should not lose the whole cluster."""

    partitions = parse_sinfo(
        "\ncompute*|64|256000|1-00:00:00\ngarbage\n|8|1000|1:00:00\n"
    )

    assert [p.name for p in partitions] == ["compute"]


def test_memory_per_core_is_worked_out_from_the_node():
    """256000 MB across 64 cores is 4000 MB, which is 3.9 GB a core."""

    partitions = parse_sinfo(TYPICAL_SINFO)

    assert partitions[0].memory_per_core_gb == pytest.approx(3.90625)


def test_memory_per_core_is_none_when_slurm_does_not_say():
    """Some configurations report no memory, and guessing silently would size jobs
    around a number nobody chose."""

    partitions = parse_sinfo("compute*|64|N/A|1-00:00:00\n")

    assert partitions[0].memory_per_core_gb is None


@pytest.mark.parametrize(
    "reported, expected",
    [
        ("1-00:00:00", "1-00:00:00"),
        ("12:00:00", "12:00:00"),
        ("infinite", "none"),
        ("UNLIMITED", "none"),
    ],
)
def test_time_limits_become_config_values(reported, expected):
    """A partition with no limit has to become the value that leaves the limit out,
    not the literal word SLURM used."""

    assert walltime_for_config(reported) == expected


@pytest.mark.parametrize(
    "hostname, expected",
    [
        # the domain is shared with the compute nodes; the host part is not
        ("login1.myhpc.ac.uk", "myhpc"),
        ("node042.myhpc.ac.uk", "myhpc"),
        # no domain, so the trailing node number comes off
        ("csf3-login01", "csf3-login"),
        ("headnode", "headnode"),
    ],
)
def test_machine_key_is_suggested_from_the_hostname(hostname, expected):
    """The key has to appear in the hostname of the compute nodes as well as this
    one, so the part that varies between nodes is what gets dropped."""

    assert suggested_machine_key(hostname) == expected


def test_generated_config_is_valid_yaml_with_the_detected_values():
    """The file is built as text so that it can carry comments, which means nothing
    checks it parses unless a test does."""

    partitions = parse_sinfo(TYPICAL_SINFO)

    config = yaml.safe_load(detected_config_text(partitions, "myhpc"))

    assert list(config) == ["myhpc"]
    hpc = config["myhpc"]["hpc"]
    assert hpc["parallel_environments"] == {"compute": [1, 64]}
    assert hpc["max_walltime"] == "1-00:00:00"
    assert hpc["memory_per_core_gb"] == pytest.approx(3.9)


def test_generated_config_covers_one_core_jobs():
    """A range that does not start at 1 makes every single core job fail, which is
    the trap the hand written configs fell into."""

    partitions = parse_sinfo(TYPICAL_SINFO)

    config = yaml.safe_load(detected_config_text(partitions, "myhpc"))
    ranges = config["myhpc"]["hpc"]["parallel_environments"].values()

    assert any(low == 1 for low, _ in ranges)


def test_generated_config_mentions_the_other_partitions():
    """They are not written as active config, because choosing which job sizes go
    where is a decision for the site, but they should not be hidden either."""

    text = detected_config_text(parse_sinfo(TYPICAL_SINFO), "myhpc")

    assert "serial" in text
    assert "gpu" in text


def test_generated_config_guesses_memory_only_when_it_must():
    """With no memory reported the file still has to be usable, but should say the
    number was assumed rather than read."""

    partitions = parse_sinfo("compute*|64|N/A|1-00:00:00\n")

    text = detected_config_text(partitions, "myhpc")
    config = yaml.safe_load(text)

    assert "guess" in text
    assert config["myhpc"]["hpc"]["memory_per_core_gb"] == 4


def test_partition_named_without_a_default_marker_keeps_its_name():
    """The * is a marker, not part of the partition name; writing it into the config
    would give sbatch a partition that does not exist."""

    partitions = parse_sinfo("compute*|64|256000|1-00:00:00\n")

    assert partitions[0].name == "compute"
    assert "compute*" not in detected_config_text(partitions, "myhpc")


def test_partition_namedtuple_is_usable_directly():
    """The parsing and the writing are separate, so a caller can build partitions
    itself (a test, or a future SGE reader) and still get a config out."""

    partitions = [Partition("batch", True, 8, 16000, "2:00:00")]

    config = yaml.safe_load(detected_config_text(partitions, "local"))

    assert config["local"]["hpc"]["parallel_environments"] == {"batch": [1, 8]}
    assert config["local"]["hpc"]["max_walltime"] == "2:00:00"
