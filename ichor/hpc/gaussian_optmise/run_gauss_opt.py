from pathlib import Path
from typing import List, Optional

from ichor.core.analysis.get_atoms import get_atoms_from_path
from ichor.core.analysis.get_path import get_file
from ichor.hpc.batch_system import JobID
from ichor.core.common.io import mkdir
from ichor.core.common.os import input_with_prefill
from ichor.hpc import FILE_STRUCTURE
from ichor.core.files import GJF, WFN, XYZ, PointsDirectory
from ichor.hpc import GLOBALS
from ichor.hpc.main.gaussian import submit_gjfs
from ichor.cli.menus.menu import Menu
from ichor.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                     SubmissionScript)
