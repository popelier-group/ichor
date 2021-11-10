from ichor.files.file import File, FileContents
from pathlib import Path
from typing import Optional
from ichor.common.types import Version
from ichor.common.functools import classproperty
from ichor.logging import logger


class AimAtom:
    def __init__(
        self,
        atom: Optional[str] = None,
        infile: Optional[Path] = None,
        outfile: Optional[Path] = None,
        time_taken: Optional[float] = None,
        integration_error: Optional[float] = None,
    ):
        self.atom = atom
        self.infile = infile
        self.outfile = outfile
        self.time_taken = time_taken
        self.integration_error = integration_error


class AIM(File, dict):
    """AIMAll Output File"""
    license_check_succeeded: Optional[bool] = FileContents
    version: Optional[Version] = FileContents
    wfn: Optional[Path] = FileContents
    extout: Optional[Path] = FileContents
    mgp: Optional[Path] = FileContents
    sum: Optional[Path] = FileContents
    sumviz: Optional[Path] = FileContents
    nproc: Optional[int] = FileContents
    nacps: Optional[int] = FileContents
    nnacps: Optional[int] = FileContents
    nbcps: Optional[int] = FileContents
    nrcps: Optional[int] = FileContents
    nccps: Optional[int] = FileContents
    cwd: Optional[Path] = FileContents

    def __init__(self, path: Path):
        File.__init__(self, path)
        dict.__init__(self)

    @classproperty
    def filetype(self) -> str:
        return ".aim"

    def _read_file(self):
        self.license_check_succeeded = False
        aim_atoms = {}
        with open(self.path, "r") as f:
            for line in f:
                if "AIMAll Professional license check succeeded." in line:
                    self.license_check_succeeded = True
                elif "AIMQB (Version" in line:
                    self.version = Version(line.split()[2])
                elif "Wavefunction File:" in line:
                    self.wfn = Path(line.split()[-1])
                elif "Number of processors used for this job =" in line:
                    self.nproc = int(line.split()[-1])
                elif "Number of NACPs  =" in line:
                    self.nacps = int(line.split()[-1])
                elif "Number of NNACPs =" in line:
                    self.nbacps = int(line.split()[-1])
                elif "Number of NBCPs  =" in line:
                    self.nbcps = int(line.split()[-1])
                elif "Number of NRCPs  =" in line:
                    self.nrcps = int(line.split()[-1])
                elif "Number of NCCPs  =" in line:
                    self.nccps = int(line.split()[-1])
                elif "Inp File:" in line:
                    aim_atoms[]
                    inpfile = Path(line.split()[-1])
                    next(f)  # wfn file
                    outfile = Path(next(f).split()[-1])
                    next(f)  # blank line
                    record = next(f).split()
                    atom, time_taken, integration_error = record[4]

        if not self.license_check_succeeded:
            logger.warning(f"AIMAll Pro License Check failed for {self.path}. AIMAll Pro Features will not be available")

