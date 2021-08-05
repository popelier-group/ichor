from pathlib import Path


def get_points_location() -> Path:
    for f in Path(".").iterdir():
        if f.suffix == ".xyz":
            return f
    raise FileNotFoundError("No Points Location Found")