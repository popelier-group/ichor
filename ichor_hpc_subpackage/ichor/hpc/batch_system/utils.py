import json
from typing import List, Optional
from pathlib import Path
from ichor.hpc.batch_system.batch_system import Job, JobID

def read_jid(jid_file: Optional[Path] = None) -> List[JobID]:
    if jid_file is None:
        from ichor.hpc import FILE_STRUCTURE
        jid_file = FILE_STRUCTURE["jid"]

    if jid_file.exists():
        with open(jid_file, "r") as f:
            try:
                jids = json.load(f)
            except json.JSONDecodeError:
                jids = []
            return [
                JobID(
                    script=jid["script"],
                    id=jid["id"],
                )
                for jid in jids
            ]

    return []


def delete_jobs():
    """Delete all jobs that were queued up to run. This function reads the FILE_STRUCTURE["jid"] file, which contains the names of all submitted jobs."""
    from ichor.hpc import FILE_STRUCTURE, BATCH_SYSTEM
    jid_file = FILE_STRUCTURE["jid"]
    jids = read_jid()
    for jid in jids:
        BATCH_SYSTEM.delete(jid)
        print(f"Deleted {jid}")

    with open(jid_file, "w") as f:
        f.write("[]")


def get_current_jobs() -> List[Job]:
    from ichor.hpc import FILE_STRUCTURE, BATCH_SYSTEM
    all_jobs = BATCH_SYSTEM.get_queued_jobs()
    ichor_jobs = read_jid(FILE_STRUCTURE["jid"])
    ichor_job_ids = [job.id for job in ichor_jobs]

    return [job for job in all_jobs if job.id in ichor_job_ids]


def display_status_of_running_jobs():
    ichor_queued_jobs = get_current_jobs()

    for job in ichor_queued_jobs:
        print(job)

    print()
    print(f"Total Jobs: {len(ichor_queued_jobs)}")
    print(
        f"Running Jobs: {len([j for j in ichor_queued_jobs if j.state == 'Running'])}"
    )
    print(
        f"Queueing Jobs: {len([j for j in ichor_queued_jobs if j.state == 'Queueing'])}"
    )
    print(
        f"Holding Jobs: {len([j for j in ichor_queued_jobs if j.state == 'Holding'])}"
    )
