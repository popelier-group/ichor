from ichor.common.io import mkdir
from ichor.file_structure import FILE_STRUCTURE


def stop():
    """Sets the stop flag in the .DATA/ACTIVE_LEARNING/stop file"""
    mkdir(FILE_STRUCTURE["stop"].parent)
    with open(FILE_STRUCTURE["stop"], "w") as f:
        f.write("1")


def start():
    """Unsets the stop flag in the .DATA/ACTIVE_LEARNING/stop file"""
    mkdir(FILE_STRUCTURE["stop"].parent)
    with open(FILE_STRUCTURE["stop"], "w") as f:
        f.write("0")


def stopped() -> bool:
    """Returns whether the current active learning process should stop"""
    if FILE_STRUCTURE["stop"].exists():
        with open(FILE_STRUCTURE["stop"], "r") as f:
            return bool(int(next(f)))  # file is either 0 or 1
    return False
