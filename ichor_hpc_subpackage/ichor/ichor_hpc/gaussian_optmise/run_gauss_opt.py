from pathlib import Path
from typing import List, Optional

from ichor.ichor_lib.analysis.get_atoms import get_atoms_from_path
from ichor.ichor_lib.analysis.get_path import get_file
from ichor.ichor_hpc.batch_system import JobID
from ichor.ichor_lib.common.io import mkdir
from ichor.ichor_lib.common.os import input_with_prefill
from ichor.ichor_hpc import FILE_STRUCTURE
from ichor.ichor_lib.files import GJF, WFN, XYZ, PointsDirectory
from ichor.ichor_hpc import GLOBALS
from ichor.ichor_hpc.main.gaussian import submit_gjfs
from ichor.ichor_cli.menus.menu import Menu
from ichor.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                     SubmissionScript)
