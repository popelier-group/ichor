from pathlib import Path

def get_points_location() -> Path:
    from ichor.hpc import GLOBALS
    """Find a .xyz file (and return the Path object pointing to it)
    that is somewhere in the directory from which ICHOR is executed. Use this files as the trajectory file
    from which training set and sample pools are made."""
    if GLOBALS.POINTS_LOCATION is not None:
        return GLOBALS.POINTS_LOCATION
    for f in Path(".").iterdir():
        if f.suffix == ".xyz":
            return f
    raise FileNotFoundError("No Points Location Found")


def set_points_location(path: Path):
    from ichor.hpc import GLOBALS
    GLOBALS.POINTS_LOCATION = path
    GLOBALS.save_to_config()
