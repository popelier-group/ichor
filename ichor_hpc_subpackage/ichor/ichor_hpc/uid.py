""" Useful functions for universally unique identifiers (UUIDs). These are used by ICHOR's file handling to write out uniquely named files which contain
the names of the files that are going to be used for jobs submitted to compute nodes. This has to be done because it is impossible to submit jobs from compute
nodes on CSF3 (which leads to the complexity of the file handling system)."""

from uuid import UUID, uuid4


def get_uid() -> UUID:
    """Get a random universally unique identifier (UUID) for a job."""
    return uuid4()


def set_uid(uid=None):
    """Set the GLOBALS Unique ID to one given by get_uid()"""
    from ichor.ichor_hpc.batch_system import BATCH_SYSTEM, NodeType
    from ichor.ichor_hpc import GLOBALS

    """ if GLOBALS.SUBMITTED is true then we are running on the compute node, when running on a compute node, it is important
    not to change the UID if it has already been set as this is what is used to write and read to datafiles"""
    if BATCH_SYSTEM.current_node() is NodeType.ComputeNode and GLOBALS.UID:
        return
    GLOBALS.UID = uid or get_uid()
