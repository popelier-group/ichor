"""These are global variables that are used and modified in the menus as needed.
This is made so that submenus can easily access specific values that
have been modified by parent menus.
"""

from pathlib import Path

# PointsDirectoryMenu options
SELECTED_POINTS_DIRECTORY_PATH: Path = Path("").absolute()

# TrainingMenu options
SELECTED_DIRECTORY_PATH: Path = Path("").absolute()

# TrajectoryMenu options
SELECTED_TRAJECTORY_PATH: Path = Path("").absolute()

# MolecularDynamicsMenu options
SELECTED_XYZ_PATH: Path = Path("").absolute()

# GaussianGJF menu
SELECTED_GJF_PATH: Path = Path("").absolute()

# SubmitCSVSMenu options
SELECTED_DATABASE_PATH: Path = Path("").absolute()

# FileConversion options
SELECTED_INPUT_FILE_PATH: Path = Path("").absolute()

# DL_FFLUX (DL_POLY) menu options
# directory where the DL_FFLUX calculation will be set up and run
SELECTED_DLPOLY_RUN_PATH: Path = Path("").absolute()
# directory containing the trained models (usually one of the 6_MODEL/xxx subfolders)
SELECTED_MODEL_DIRECTORY_PATH: Path = Path("").absolute()

# DL_FFLUX robustness check (analysis menu) options
# base directory in which the per-seed RUN* directories are created
SELECTED_DLPOLY_ROBUSTNESS_PATH: Path = Path("").absolute()
# diversity-sampled trajectory (.xyz) from which the seed geometries are taken (in order)
SELECTED_DLPOLY_SEED_TRAJECTORY_PATH: Path = Path("").absolute()
# reference (usually optimised) geometry whose bond lengths define an intact molecule,
# used by the stability check of the finished runs
SELECTED_DLPOLY_REFERENCE_GEOMETRY_PATH: Path = Path("").absolute()
