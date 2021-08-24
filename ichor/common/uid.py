""" Useful functions for universally unique identifiers (UUIDs). These are used by ICHOR's file handling to write out uniquely named files which contain
the names of the files that are going to be used for jobs submitted to compute nodes. This has to be done because it is impossible to submit jobs from compute
nodes on CSF3 (which leads to the complexity of the file handling system)."""

from uuid import UUID, uuid4


def get_uid() -> UUID:
    """ Get a random universally unique identifier (UUID) for a job."""
    return uuid4()


def set_uid(uid=None):
    """ Set the GLOBALS Unique ID to one given by get_uid()"""
    from ichor.globals import GLOBALS

    # matt_todo: GLOBALS.SUBMITTED is set to False (and says to not change), so not sure what this is doing
    if GLOBALS.SUBMITTED and GLOBALS.UID:
        return
    GLOBALS.UID = uid or get_uid()
