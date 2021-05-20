from pathlib import Path
from typing import Optional

from ichor.batch_system import JobID
from ichor.points import PointsDirectory
from ichor.submission_script import (SCRIPT_NAMES, AIMAllCommand,
                                     SubmissionScript)


def auto_run_aimall(
    aimall_directory: Path, hold: Optional[JobID] = None
) -> Optional[JobID]:
    script_name = SCRIPT_NAMES["aimall"]
    points = PointsDirectory(aimall_directory)
    aimall_script = SubmissionScript(script_name)
    for point in points:
        if point.wfn:
            aimall_script.add_command(AIMAllCommand(point.wfn.path))
        elif point.gjf:
            aimall_script.add_command(
                AIMAllCommand(point.gjf.path.with_suffix(".wfn"))
            )
    aimall_script.write()
    return aimall_script.submit(hold=hold)
