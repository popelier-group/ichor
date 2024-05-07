from pathlib import Path

from ichor.core.files import XYZ

wfn = XYZ(
    Path("example_files")
    / "example_points_directory"
    / "WATER_MONOMER.pointsdir"
    / "WATER_MONOMER0000.pointdir"
    / "WATER_MONOMER0000.xyz"
)

print(wfn.atoms)
