"""Per-point progress, using recorded array tasks and calculation outputs."""

import contextlib
import io
import json
from pathlib import Path


def record_submission(job, commands):
    records = {}
    for task, command in enumerate(commands, 1):
        software = {"GaussianCommand": "gaussian", "AimallCommand": "aimall",
                    "AIMAllCommand": "aimall"}.get(type(command).__name__)
        if software is None:
            continue
        point = Path(command.data[0]).resolve().parent
        if point.suffix != ".pointdir" or point.parent.suffix != ".pointsdir":
            continue
        records.setdefault(point.parent, []).append(
            (point.name, software, {"id": str(job.id), "task": task})
        )
    for directory, entries in records.items():
        path = directory / ".ichor-status.json"
        data = json.loads(path.read_text()) if path.exists() else {}
        for point, software, record in entries:
            data.setdefault(software, {})[point] = record
        path.write_text(json.dumps(data, indent=2))


def calculation_status(directory, software, jobs=None):
    directory = Path(directory)
    path = directory / ".ichor-status.json"
    records = json.loads(path.read_text()).get(software, {}) if path.exists() else {}
    if jobs is None:
        jobs = []
        if records:
            import ichor.hpc.global_variables as settings

            jobs = settings.BATCH_SYSTEM.get_queued_jobs()
    states = {(str(job.id), str(job.task_id or 1)): job.state for job in jobs}
    counts = dict(completed=0, failed=0, running=0, pending=0, unknown=0, total=0)
    for point in sorted(directory.glob("*.pointdir")):
        if not point.is_dir():
            continue
        counts["total"] += 1
        record = records.get(point.name)
        state = states.get((record["id"], str(record["task"]))) if record else None
        # Active retries take precedence over outputs from previous attempts.
        if state is not None:
            category = "running" if state == "Running" else "failed" if state == "Error" else "pending"
        elif software == "gaussian":
            outputs = list(point.glob("*.gau")) + list(point.glob("*.gaussianoutput"))
            output = max(outputs, key=lambda p: p.stat().st_mtime) if outputs else None
            text = output.read_text(errors="replace") if output else ""
            if "Normal termination of Gaussian" in text:
                category = "completed"
            elif "Error termination" in text or record:
                category = "failed"
            else:
                category = "unknown" if output else "pending"
        else:
            from ichor.core.useful_functions.check_aimall_completed import aimall_completed

            complete = False
            with contextlib.redirect_stdout(io.StringIO()):
                for wfn in point.glob("*.wfn"):
                    complete = aimall_completed(wfn)
                    if complete:
                        break
            category = "completed" if complete else "failed" if record else "unknown" if list(point.glob("*.aim")) else "pending"
        counts[category] += 1
    return counts


def print_status(directory, software):
    counts = calculation_status(directory, software)
    name = "Gaussian" if software == "gaussian" else "AIMAll"
    print(f"\u2713 {name:<20} {counts['completed']} / {counts['total']}")
    for symbol, category in (("!", "failed"), ("\u25cf", "running"), ("\u25cb", "pending"), ("?", "unknown")):
        if counts[category]:
            print(f"{symbol} {name:<20} {counts[category]} {category}")
    return counts
