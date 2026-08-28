"""Tests for where ichor looks for, and writes, its config file.

These matter because getting them wrong either loses an existing user's config or
silently reads a different file than the one they edited.
"""

import pytest

from ichor.hpc.config_file import (
    config_search_locations,
    default_config_path,
    find_config_file,
    legacy_config_path,
    migrate_legacy_config,
    write_config_template,
    xdg_config_home,
)


@pytest.fixture
def home(tmp_path, monkeypatch):
    """Points the home directory at a temporary directory and clears the
    environment variables that the config lookup reads, so that a test never sees
    the config file of whoever is running it."""

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("ICHOR_CONFIG", raising=False)

    return tmp_path


def write(path, text):
    """Writes ``text`` to ``path``, creating the parent directories."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)

    return path


def test_xdg_config_home_defaults_to_dot_config(home):
    """Without XDG_CONFIG_HOME the specified default of ~/.config is used."""

    assert xdg_config_home() == home / ".config"


def test_xdg_config_home_is_used_when_set(home, tmp_path, monkeypatch):
    """An absolute XDG_CONFIG_HOME replaces ~/.config."""

    elsewhere = tmp_path / "somewhere"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(elsewhere))

    assert xdg_config_home() == elsewhere
    assert default_config_path() == elsewhere / "ichor" / "config.yaml"


def test_relative_xdg_config_home_is_ignored(home, monkeypatch):
    """The specification says a relative XDG_CONFIG_HOME is invalid, so the default
    is used rather than resolving it against the working directory."""

    monkeypatch.setenv("XDG_CONFIG_HOME", "relative/path")

    assert xdg_config_home() == home / ".config"


def test_no_config_anywhere_returns_none(home):
    """A machine with no config file at all is not an error, so that ichor can be
    imported in order to be told to make one."""

    assert find_config_file() is None


def test_config_found_in_xdg_location(home):
    """The XDG location is the one ichor is expected to read."""

    expected = write(home / ".config" / "ichor" / "config.yaml", "xdg: true")

    assert find_config_file() == expected


def test_legacy_config_is_still_found(home):
    """An existing installation keeps working after the config location moved."""

    expected = write(home / "ichor_config.yaml", "legacy: true")

    with pytest.warns(DeprecationWarning):
        assert find_config_file() == expected


def test_xdg_location_wins_over_legacy(home):
    """Someone who has migrated but left the old file behind reads the new one."""

    write(home / "ichor_config.yaml", "legacy: true")
    expected = write(home / ".config" / "ichor" / "config.yaml", "xdg: true")

    assert find_config_file() == expected


def test_environment_variable_wins_over_both(home, tmp_path, monkeypatch):
    """An explicitly configured path overrides both default locations."""

    write(home / "ichor_config.yaml", "legacy: true")
    write(home / ".config" / "ichor" / "config.yaml", "xdg: true")
    explicit = write(tmp_path / "explicit.yaml", "explicit: true")
    monkeypatch.setenv("ICHOR_CONFIG", str(explicit))

    assert find_config_file() == explicit


def test_missing_environment_variable_target_does_not_fall_through(
    home, tmp_path, monkeypatch
):
    """A typo in ICHOR_CONFIG must not silently read a different config, as the
    job would then be submitted with settings the user did not ask for."""

    write(home / ".config" / "ichor" / "config.yaml", "xdg: true")
    monkeypatch.setenv("ICHOR_CONFIG", str(tmp_path / "does_not_exist.yaml"))

    assert find_config_file() is None


def test_search_locations_are_reported_in_order(home):
    """The locations are reported so that a user who has no config can be told
    every place one could go."""

    locations = config_search_locations()

    assert len(locations) == 3
    assert "ICHOR_CONFIG" in locations[0]
    assert str(default_config_path()) in locations[1]
    assert str(legacy_config_path()) in locations[2]


def test_write_config_template_creates_parent_directories(home):
    """~/.config/ichor will not exist on a fresh account."""

    destination = default_config_path()
    assert not destination.parent.exists()

    write_config_template(destination)

    assert destination.exists()
    # the packaged template is the example config, so it names the machines
    assert "csf3" in destination.read_text()


def test_write_config_template_refuses_to_overwrite(home):
    """An edited config must not be replaced by the example by accident."""

    destination = write(default_config_path(), "mine: true")

    with pytest.raises(FileExistsError):
        write_config_template(destination)

    assert destination.read_text() == "mine: true"


def test_write_config_template_overwrites_when_forced(home):
    """Overwriting is still possible when it is asked for explicitly."""

    destination = write(default_config_path(), "mine: true")

    write_config_template(destination, overwrite=True)

    assert "csf3" in destination.read_text()


def test_migrate_moves_the_legacy_config(home):
    """Migrating keeps the user's own settings rather than replacing them with
    the example config."""

    write(home / "ichor_config.yaml", "mine: true")

    destination = migrate_legacy_config(default_config_path())

    assert destination.read_text() == "mine: true"
    assert not legacy_config_path().exists()


def test_migrate_without_a_legacy_config_raises(home):
    """Asking to migrate when there is nothing to migrate is an error rather than
    a silently empty config."""

    with pytest.raises(FileNotFoundError):
        migrate_legacy_config(default_config_path())


def test_migrate_refuses_to_overwrite(home):
    """The config already at the new location is the one being used, so it must
    not be replaced by an older one."""

    write(home / "ichor_config.yaml", "old: true")
    destination = write(default_config_path(), "current: true")

    with pytest.raises(FileExistsError):
        migrate_legacy_config(destination)

    assert destination.read_text() == "current: true"
    assert legacy_config_path().exists()
