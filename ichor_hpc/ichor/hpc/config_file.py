"""Locating and creating ichor's configuration file.

ichor reads its per-machine settings (module names, executable paths, parallel
environments) from a YAML file. Historically that file had to be at
``~/ichor_config.yaml``. It now lives in ``~/.config/ichor/config.yaml``, which
is where the XDG Base Directory specification says user configuration belongs,
so that it sits alongside the configuration of other software rather than at the
top of the home directory.

The old location is still read so that existing installations keep working, but
a warning is issued asking for the file to be moved.
"""

import os
import shutil
import warnings

from importlib.resources import as_file, files
from pathlib import Path
from typing import List, Optional

# the environment variable which, if set, points directly at a config file and
# overrides both of the locations below
CONFIG_ENVIRONMENT_VARIABLE = "ICHOR_CONFIG"

# the directory name used underneath $XDG_CONFIG_HOME (or ~/.config)
CONFIG_DIRECTORY_NAME = "ichor"
CONFIG_FILE_NAME = "config.yaml"

# what the config file used to be called, directly in the home directory
LEGACY_CONFIG_FILE_NAME = "ichor_config.yaml"


def xdg_config_home() -> Path:
    """Returns the base directory for user configuration files, as defined by the
    XDG Base Directory specification. ``$XDG_CONFIG_HOME`` is used if it is set to
    an absolute path, otherwise the specified default of ``~/.config`` is used.

    :return: The directory that per-user configuration is stored under.
    """

    xdg = os.environ.get("XDG_CONFIG_HOME")

    # the specification says a relative path is invalid and must be ignored
    if xdg and Path(xdg).is_absolute():
        return Path(xdg)

    return Path.home() / ".config"


def legacy_config_path() -> Path:
    """Returns the path the config file used to have to be at, before it moved to
    the XDG config directory. Resolved on each call rather than at import so that
    it follows the home directory rather than freezing whatever it was at startup.

    :return: ``~/ichor_config.yaml``.
    """

    return Path.home() / LEGACY_CONFIG_FILE_NAME


def default_config_path() -> Path:
    """Returns the path that the config file is written to and read from, ignoring
    the environment variable override and the legacy location.

    :return: ``$XDG_CONFIG_HOME/ichor/config.yaml``, or
        ``~/.config/ichor/config.yaml`` if ``$XDG_CONFIG_HOME`` is not set.
    """

    return xdg_config_home() / CONFIG_DIRECTORY_NAME / CONFIG_FILE_NAME


def config_path_from_environment() -> Optional[Path]:
    """Returns the config path given by the ``ICHOR_CONFIG`` environment variable.

    :return: The path the variable is set to, or None if it is unset or empty.
    """

    from_environment = os.environ.get(CONFIG_ENVIRONMENT_VARIABLE)

    if from_environment:
        return Path(from_environment).expanduser()


def config_search_locations() -> List[str]:
    """Returns human readable descriptions of every place that is searched for a
    config file, in the order they are searched. Used to tell the user where the
    file can go when none was found.

    :return: A list of descriptions, most preferred first.
    """

    return [
        f"the {CONFIG_ENVIRONMENT_VARIABLE} environment variable (currently unset)"
        if config_path_from_environment() is None
        else f"{CONFIG_ENVIRONMENT_VARIABLE}={config_path_from_environment()}",
        str(default_config_path()),
        f"{legacy_config_path()} (deprecated)",
    ]


def find_config_file() -> Optional[Path]:
    """Finds the config file to use, searching, in order, the path given by the
    ``ICHOR_CONFIG`` environment variable, the XDG config location, and finally the
    location the file used to be kept in.

    Finding the file in the legacy location warns, but still uses it, so that
    existing installations are not broken by the move.

    :return: The path of the first config file that exists, or None if there is
        no config file in any of the searched locations.
    """

    from_environment = config_path_from_environment()

    # an explicitly configured path is used even if it does not exist, so that a
    # typo in the variable is reported against the path the user actually gave
    # rather than silently falling through to a different file
    if from_environment is not None:
        if from_environment.exists():
            return from_environment
        return None

    if default_config_path().exists():
        return default_config_path()

    if legacy_config_path().exists():
        warnings.warn(
            f"Reading the ichor config from the deprecated location {legacy_config_path()}. "
            f"Move it to {default_config_path()} with:\n"
            f"    mkdir -p {default_config_path().parent}\n"
            f"    mv {legacy_config_path()} {default_config_path()}\n"
            "or run `ichor-config-init --migrate` to do it for you.",
            DeprecationWarning,
            stacklevel=2,
        )
        return legacy_config_path()


def config_template_text() -> str:
    """Returns the contents of the example config file that ships with ichor.hpc.

    :return: The text of the packaged config template.
    """

    template = files("ichor.hpc") / "data" / "config_template.yaml"

    with as_file(template) as template_path:
        return Path(template_path).read_text()


def write_config_template(destination: Path, overwrite: bool = False) -> Path:
    """Writes the packaged config template out to ``destination``, creating the
    parent directory if it does not exist.

    :param destination: The path to write the config file to.
    :param overwrite: Whether to replace an existing file, defaults to False.
    :raises FileExistsError: If ``destination`` exists and ``overwrite`` is False.
    :return: The path that was written to.
    """

    if destination.exists() and not overwrite:
        raise FileExistsError(
            f"{destination} already exists. Pass --force to overwrite it."
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(config_template_text())

    return destination


def migrate_legacy_config(destination: Path, overwrite: bool = False) -> Path:
    """Moves a config file from the location it used to be kept in to the location
    it is now read from.

    :param destination: The path to move the legacy config file to.
    :param overwrite: Whether to replace an existing file at ``destination``,
        defaults to False.
    :raises FileNotFoundError: If there is no config file in the legacy location.
    :raises FileExistsError: If ``destination`` exists and ``overwrite`` is False.
    :return: The path that was moved to.
    """

    if not legacy_config_path().exists():
        raise FileNotFoundError(
            f"There is no config file at {legacy_config_path()} to migrate."
        )

    if destination.exists() and not overwrite:
        raise FileExistsError(
            f"{destination} already exists. Pass --force to overwrite it."
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(legacy_config_path()), str(destination))

    return destination
