"""These are global variables that are used and modified in the menus as needed.
    This is made so that submenus can easily access specific values that
    have been modified by parent menus.
"""

from pathlib import Path

SELECTED_POINTS_DIRECTORY_PATH: Path = Path("").absolute()