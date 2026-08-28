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


def main(argv: Optional[List[str]] = None) -> int:
    """Creates ichor's config file and tells the user what to do with it.

    :param argv: The arguments to parse, defaults to the process arguments.
    :return: 0 if a config file was created, 1 if it could not be.
    """

    arguments = parse_arguments(argv)
    destination = resolve_destination(arguments.path)

    if arguments.template and arguments.migrate:
        print("--template and --migrate cannot be used together.", file=sys.stderr)
        return 1

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
