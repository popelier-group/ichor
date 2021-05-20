from pathlib import Path
from typing import Optional

from ichor.batch_system import JobID
from ichor.points import PointsDirectory
from ichor.submission_script import (SCRIPT_NAMES, GaussianCommand,
                                     SubmissionScript)


def auto_run_gaussian(
    gaussian_directory: Path, hold: Optional[JobID] = None
) -> Optional[JobID]:
    script_name = SCRIPT_NAMES["gaussian"]
    points = PointsDirectory(gaussian_directory)
    gauss_script = SubmissionScript(script_name)
    for point in points:
        gauss_script.add_command(GaussianCommand(point.gjf.path))
    gauss_script.write()
    return gauss_script.submit(hold=hold)
