"""Tests for the filesystem helpers, in particular for copying into a directory which
already holds something.

The dataset preparation copies the selected folder of csv files into the directory it
sets a job up in, and that directory is the same one every time a system is prepared, so
the second run for a system copies into a directory which the first run already filled.
"""

from ichor.core.common.io import copytree


def make_tree(path, contents: dict):
    """Writes a tree of files, given as {name: text} with nested dicts for folders."""

    path.mkdir(parents=True, exist_ok=True)
    for name, value in contents.items():
        if isinstance(value, dict):
            make_tree(path / name, value)
        else:
            (path / name).write_text(value)


def read_tree(path) -> dict:
    """Reads a tree of files back, in the shape :func:`make_tree` writes them."""

    contents = {}
    for item in sorted(path.iterdir()):
        contents[item.name] = read_tree(item) if item.is_dir() else item.read_text()

    return contents


def test_copying_into_an_empty_directory(tmp_path):

    make_tree(tmp_path / "src", {"o1.csv": "one", "iqa": {"h2.csv": "two"}})
    (tmp_path / "dst").mkdir()

    copytree(tmp_path / "src", tmp_path / "dst")

    assert read_tree(tmp_path / "dst") == {"o1.csv": "one", "iqa": {"h2.csv": "two"}}


def test_copying_into_a_directory_which_already_holds_files(tmp_path):
    """What is already there is kept, and what the source holds of the same name
    replaces it."""

    make_tree(tmp_path / "src", {"o1.csv": "new", "h2.csv": "new"})
    make_tree(tmp_path / "dst", {"o1.csv": "old", "kept.csv": "old"})

    copytree(tmp_path / "src", tmp_path / "dst")

    assert read_tree(tmp_path / "dst") == {
        "o1.csv": "new",
        "h2.csv": "new",
        "kept.csv": "old",
    }


def test_copying_into_a_directory_which_already_holds_subdirectories(tmp_path):
    """A folder of per-property subfolders copied on top of one which is already there
    merges into it, rather than failing because the subfolder exists (which is what
    stopped a system being prepared a second time)."""

    make_tree(
        tmp_path / "src",
        {"iqa": {"o1.csv": "new", "h2.csv": "new"}, "q00": {"o1.csv": "new"}},
    )
    make_tree(
        tmp_path / "dst",
        {"iqa": {"o1.csv": "old", "kept.csv": "old"}},
    )

    copytree(tmp_path / "src", tmp_path / "dst")

    assert read_tree(tmp_path / "dst") == {
        "iqa": {"o1.csv": "new", "h2.csv": "new", "kept.csv": "old"},
        "q00": {"o1.csv": "new"},
    }
