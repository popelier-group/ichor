import json

from ichor.batch_system import BATCH_SYSTEM, JobID
from ichor.menu import Menu


def delete_jobs():
    """Delete all jobs that were queued up to run. This function reads the GLOBALS.FILE_STRUCTURE["jid"] file, which contains the names of all submitted jobs."""
    from ichor.file_structure import FILE_STRUCTURE

    jid_file = FILE_STRUCTURE["jid"]
    if jid_file.exists():
        with open(jid_file, "r") as f:
            try:
                jids = json.load(f)
            except json.JSONDecodeError:
                jids = []
            for jid in jids:
                jid = JobID(
                    script=jid["script"],
                    id=jid["id"],
                    instance=jid["instance"],
                )
                BATCH_SYSTEM.delete(jid)
                print(f"Deleted {jid}")

        with open(jid_file, "w") as f:
            f.write("[]")


def queue_menu():
    """Handler function which opens up a menu containing options relating to jobs."""
    with Menu("Queue Meu", space=True, back=True, exit=True) as menu:
        menu.add_option("del", "Delete currently running jobs", delete_jobs)
