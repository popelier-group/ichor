"""These are global variables that are used and modified in the menus as needed.
    This is made so that submenus can easily access specific values that
    have been modified by parent menus.
"""

from pathlib import Path

# PointsDirectoryMenu options
SELECTED_POINTS_DIRECTORY_PATH: Path = Path("").absolute()

# TrajectoryMenu options
SELECTED_TRAJECTORY_PATH: Path = Path("").absolute()

# MolecularDynamicsMenu options
SELECTED_XYZ_PATH: Path = Path("").absolute()

# SubmitCSVSMenu options
SELECTED_DATABASE_PATH: Path = Path("").absolute()

# FileConversion options
SELECTED_INPUT_FILE_PATH: Path = Path("").absolute()
