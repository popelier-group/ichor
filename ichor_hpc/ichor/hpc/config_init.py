"""The ``ichor-config-init`` command, which puts a config file in the place that
ichor looks for one.

Without a config file ichor.hpc cannot work out which machine it is on, which
modules to load, or where any of the computational chemistry programs are, so
creating one is the first thing to do after installing ichor.
"""

import argparse
import sys

from pathlib import Path
from typing import List, Optional

from ichor.hpc.config_file import (
    config_path_from_environment,
    default_config_path,
    legacy_config_path,
    migrate_legacy_config,
    write_config_template,
)

from ichor.hpc.detect_hpc import (
    default_partition,
    detect_partitions,
    detected_config_text,
    DetectionUnavailable,
    suggested_machine_key,
)


def parse_arguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parses the command line arguments of ``ichor-config-init``.

    :param argv: The arguments to parse, defaults to the process arguments.
    :return: The parsed arguments.
    """

    parser = argparse.ArgumentParser(
        prog="ichor-config-init",
        description=(
            "Create ichor's config file. If a config file is found in the location "
            "ichor used to read it from (~/ichor_config.yaml) it is moved to the new "
            "location, otherwise an example config file is written out for you to edit."
        ),
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help=(
            "Where to write the config file. Defaults to the ICHOR_CONFIG environment "
            "variable if it is set, and to ~/.config/ichor/config.yaml otherwise."
        ),
    )
    parser.add_argument(
        "--template",
        action="store_true",
        help=(
            "Always write out the example config file, even if there is a config file "
            "in the old location that could be moved instead."
        ),
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help=(
            "Move the config file from the location ichor used to read it from "
            "(~/ichor_config.yaml), failing if there is not one there. This is what "
            "happens by default when such a file exists, so it is only needed to turn "
            "a missing legacy file into an error rather than a fresh template."
        ),
    )
    parser.add_argument(
        "--detect",
        action="store_true",
        help=(
            "Read the queue settings of this cluster with sinfo and write a config "
            "with the hpc block already filled in. SLURM only, and has to be run "
            "somewhere sinfo works, which usually means a login node."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the config file if one is already there.",
    )

    return parser.parse_args(argv)


def resolve_destination(explicit_path: Optional[Path]) -> Path:
    """Works out where the config file should be written.

    :param explicit_path: A path given on the command line, or None.
    :return: The path given on the command line if there was one, otherwise the
        path that ``ICHOR_CONFIG`` points at, otherwise the default location.
    """

    if explicit_path is not None:
        return explicit_path.expanduser()

    from_environment = config_path_from_environment()

    if from_environment is not None:
        return from_environment

    return default_config_path()


def write_detected_config(destination: Path, overwrite: bool = False) -> int:
    """Reads this cluster's queue settings and writes a config built around them.

    :param destination: The path to write the config file to.
    :param overwrite: Whether to replace an existing file, defaults to False.
    :return: 0 if the config was written, 1 if it could not be.
    """

    try:
        partitions = detect_partitions()
    except DetectionUnavailable as error:
        print(error, file=sys.stderr)
        return 1

    machine_key = suggested_machine_key()

    try:
        if destination.exists() and not overwrite:
            raise FileExistsError(
                f"{destination} already exists. Pass --force to overwrite it."
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(detected_config_text(partitions, machine_key))
    except FileExistsError as error:
        print(error, file=sys.stderr)
        return 1

    chosen = default_partition(partitions)
    print(f"Wrote a config for this cluster to {destination}")
    print(
        f"\nRead from sinfo: {len(partitions)} partition(s), of which {chosen.name} "
        f"is the default,\nwith {chosen.cores_per_node} cores per node and a time "
        f"limit of {chosen.time_limit}."
    )
    print(
        "\nTwo things still need you:\n"
        f"  - the machine key, which was guessed as '{machine_key}' from the "
        "hostname. It has to\n    appear in the hostname of the compute nodes too, "
        "which differ from this one.\n"
        "  - the software block, which says where each program is and which module "
        "loads it.\n    sinfo cannot know any of that."
    )

    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Creates ichor's config file and tells the user what to do with it.

    :param argv: The arguments to parse, defaults to the process arguments.
    :return: 0 if a config file was created, 1 if it could not be.
    """

    arguments = parse_arguments(argv)
    destination = resolve_destination(arguments.path)

    exclusive = [
        name for name in ("template", "migrate", "detect") if getattr(arguments, name)
    ]
    if len(exclusive) > 1:
        given = " and ".join(f"--{name}" for name in exclusive)
        print(f"{given} cannot be used together.", file=sys.stderr)
        return 1

    if arguments.detect:
        return write_detected_config(destination, overwrite=arguments.force)

    # moving an existing config is preferred over writing a fresh template, as the
    # existing one has already been filled in for the machines the user runs on
    should_migrate = arguments.migrate or (
        not arguments.template
        and legacy_config_path().exists()
        and legacy_config_path() != destination
    )

    try:
        if should_migrate:
            migrate_legacy_config(destination, overwrite=arguments.force)
            print(f"Moved {legacy_config_path()} to {destination}")
        else:
            write_config_template(destination, overwrite=arguments.force)
            print(f"Wrote an example ichor config file to {destination}")
            print(
                "\nEdit it before submitting any jobs. Every top level key is the name "
                "of a machine,\nwhich ichor matches against the hostname, so the block "
                "for the cluster you are on\nneeds to name the modules to load and the "
                "paths to the programs you want to run."
            )
    except (FileExistsError, FileNotFoundError) as error:
        print(error, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
