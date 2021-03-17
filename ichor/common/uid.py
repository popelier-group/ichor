from uuid import uuid4, UUID


def get_uid() -> UUID:
    return uuid4()


def set_uid(uid=None):
    from ..globals import GLOBALS
    if GLOBALS.SUBMITTED and GLOBALS.UID:
        return
    GLOBALS.UID = uid if uid else get_uid()
