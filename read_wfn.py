from pathlib import Path

from ichor.core.files import WFN

wfn = WFN(
    Path("example_files")
    / "example_points_directory"
    / "WATER_MONOMER.pointsdir"
    / "WATER_MONOMER0000.pointdir"
    / "WATER_MONOMER0000.wfn"
)

print(wfn.virial_ratio)
