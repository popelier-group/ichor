"""These are global variables that are used and modified in the menus as needed.
This is made so that submenus can easily access specific values that
have been modified by parent menus.
"""

from pathlib import Path
from typing import List

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

# Model-analysis menu options
SELECTED_MODELS_PATH: Path = Path("").absolute()
# which held-out split the analysis is run against, kept here (rather than only on the
# model-analysis menu) so that its submenus are run against the same split
SELECTED_MODEL_SET_TYPE: str = "EXT_VALIDATION_SET"

# DL_FFLUX (DL_POLY) menu options
# directory where the DL_FFLUX calculation will be set up and run
SELECTED_DLPOLY_RUN_PATH: Path = Path("").absolute()
# directory containing the trained models (usually one of the 6_MODEL/xxx subfolders)
SELECTED_MODEL_DIRECTORY_PATH: Path = Path("").absolute()

# DL_FFLUX condensed phase menu options
# directory where the condensed phase DL_FFLUX calculation will be set up and run
SELECTED_DLPOLY_CONDENSED_RUN_PATH: Path = Path("").absolute()
# .xyz file holding the packed box of molecules (e.g. as written by Packmol)
SELECTED_DLPOLY_CONDENSED_XYZ_PATH: Path = Path("").absolute()
# directories containing the trained models, one per molecular species in the box. They are
# added one at a time, which is why this starts out empty rather than as a placeholder path.
SELECTED_DLPOLY_CONDENSED_MODEL_PATHS: List[Path] = []

# DL_FFLUX HISTORY extraction (FFLUX calculations menu) options
# HISTORY trajectory written by a finished DL_FFLUX run
SELECTED_DLPOLY_HISTORY_PATH: Path = Path("").absolute()
# .xyz file the geometries taken out of that HISTORY file are written to
SELECTED_DLPOLY_HISTORY_XYZ_PATH: Path = Path("").absolute()

# DL_FFLUX robustness check (analysis menu) options
# base directory in which the per-seed RUN* directories are created
SELECTED_DLPOLY_ROBUSTNESS_PATH: Path = Path("").absolute()
# diversity-sampled trajectory (.xyz) from which the seed geometries are taken (in order)
SELECTED_DLPOLY_SEED_TRAJECTORY_PATH: Path = Path("").absolute()
# reference (usually optimised) geometry whose bond lengths define an intact molecule,
# used by the stability check of the finished runs
SELECTED_DLPOLY_REFERENCE_GEOMETRY_PATH: Path = Path("").absolute()

# DL_FFLUX single point calculations (analysis menu) options
# base directory in which the per-geometry POINT* directories are created
SELECTED_DLPOLY_SINGLE_POINT_PATH: Path = Path("").absolute()
# .xyz file holding the geometries to calculate single points for
SELECTED_DLPOLY_SINGLE_POINT_TRAJECTORY_PATH: Path = Path("").absolute()
