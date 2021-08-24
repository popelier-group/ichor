from ichor.common.functools import classproperty

_level = 0
_locked = False


class DataLock:
    """ Used to lock the datafiles which are used to write out submission scripts for jobs."""
    @classproperty
    def locked(self):
        return _locked

    @classmethod
    def lock(cls):
        global _locked
        _locked = True

    @classmethod
    def unlock(cls):
        global _locked
        _locked = False

    def __enter__(self):
        global _locked
        global _level
        _locked = True
        _level += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _locked
        global _level
        _level -= 1 if _level > 0 else 0
        _locked = False if _level == 0 else _locked
