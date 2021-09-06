from ichor.common.functools import classproperty

_level = 0
_locked = False


class DataLock:
    """
    Used to lock writing to datafiles which are used during writing out submission scripts for jobs.

    DataLock is required to prevent a data race when submitting jobs to the batch system during an auto run procedure

      | Login                     | Datafile                   | Compute
    -----------------------------------------------------------------------------------
      | Submit Job1 to write DF1  |                            |
    T |                           |                            | Job1 runs on compute
    I |                           | DF1 written from compute   |
    M | Submit Job2 that uses DF1 |                            |
    E |                           | DF1 overwritten from login |
      |                           |                            | Job2 runs on compute

    As the datafile for a submission script (DF1 in this case) is written when writing a submission script
    in order to keep the code between running on login and compute nodes identical, DF1 will be overwritten
    when submitting Job2 in the case above. Unfortunately if the previously submitted Job1 has already ran
    and written DF1 from the compute node, the data would be overwritten from submitting Job2 on the login
    node. Consequently, when Job2 runs on the compute node, the data it would read from DF1 wouldn't be the
    correct data written by Job1 but instead garbage data written whilst submitting Job2 from the login node.

    To prevent this data race from occuring, DataLock prevents writing datafiles from the login node which
    turns our above scenario into the following

      | Login                     | Datafile                   | Compute
    -----------------------------------------------------------------------------------
    T | Submit Job1 to write DF1  |                            |
    I |                           |                            | Job1 runs on compute
    M |                           | DF1 written from compute   |
    E | Submit Job2 that uses DF1 |                            |
      |                           |                            | Job2 runs on compute

    """

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
