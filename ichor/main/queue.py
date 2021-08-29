from ichor.menu import Menu
from ichor.batch_system import JobID, BATCH_SYSTEM
import json


def delete_jobs():
    """ Delete all jobs that were queued up to run. This function reads the GLOBALS.FILE_STRUCTURE["jid"] file, which contains the names of all submitted jobs."""
    from ichor.globals import GLOBALS
    jid_file = GLOBALS.FILE_STRUCTURE["jid"]
    if jid_file.exists():
        with open(jid_file, "r") as f:
            jids = json.load(f)
            for jid in jids:
                jid = JobID(script=jid["script"], id=jid["id"], instance=jid["instance"])
                BATCH_SYSTEM.delete(jid)
                print(f"Deleted {jid}")


def queue_menu():
    """ Handler function which opens up a menu containing options relating to jobs."""
    with Menu("Queue Menu", space=True, back=True, exit=True) as menu:
        menu.add_option("del", "Delete currently running jobs", delete_jobs)
