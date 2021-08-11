from uuid import UUID, uuid4


def get_uid() -> UUID:
    """ Get a random universally unique identifier (UUID) for a job."""
    return uuid4()


def set_uid(uid=None):
    from ichor.globals import GLOBALS

    # matt_todo: GLOBALS.SUBMITTED is set to False (and says to not change), so not sure what this is doing
    if GLOBALS.SUBMITTED and GLOBALS.UID:
        return
    GLOBALS.UID = uid or get_uid()
