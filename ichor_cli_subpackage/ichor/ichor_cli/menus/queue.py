import json
from pathlib import Path
from typing import List

from ichor.batch_system import BATCH_SYSTEM, Job, JobID
from ichor_hpc.file_structure.file_structure import FILE_STRUCTURE
from ichor.ichor_cli.menus.menu import Menu


def read_jid(jid_file: Path = FILE_STRUCTURE["jid"]) -> List[JobID]:
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
                    instance=jid["instance"],
                )
                for jid in jids
            ]

    return []


def delete_jobs():
    """Delete all jobs that were queued up to run. This function reads the GLOBALS.FILE_STRUCTURE["jid"] file, which contains the names of all submitted jobs."""
    jid_file = FILE_STRUCTURE["jid"]
    jids = read_jid()
    for jid in jids:
        BATCH_SYSTEM.delete(jid)
        print(f"Deleted {jid}")

    with open(jid_file, "w") as f:
        f.write("[]")


def get_current_jobs() -> List[Job]:
    all_jobs = BATCH_SYSTEM.get_queued_jobs()
    ichor_jobs = read_jid(FILE_STRUCTURE["jid"])
    ichor_job_ids = [job.id for job in ichor_jobs]

    return [job for job in all_jobs if job.id in ichor_job_ids]


def get_status_of_running_jobs():
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


def queue_menu():
    """Handler function which opens up a menu containing options relating to jobs."""
    with Menu("Queue Meu", space=True, back=True, exit=True) as menu:
        menu.add_option("del", "Delete currently running jobs", delete_jobs)
        menu.add_option(
            "stat",
            "Print status of currently running jobs",
            get_status_of_running_jobs,
            wait=True,
        )
