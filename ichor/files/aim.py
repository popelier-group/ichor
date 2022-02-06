from http.client import LineTooLong
from pathlib import Path
from pickle import GLOBAL
from typing import Optional, Union

from ichor.common.functools import classproperty
from ichor.common.str import get_digits
from ichor.common.types import Version
from ichor.files.file import File, FileContents
from ichor.globals import GLOBALS


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
    output_file: Optional[Path] = FileContents
    cwd: Optional[Path] = FileContents

    def __init__(self, path: Path):
        File.__init__(self, path)
        dict.__init__(self)

    @classproperty
    def filetype(self) -> str:
        return ".aim"

    def _read_file(self):

        self.license_check_succeeded = False

        with open(self.path, "r") as f:
            for line in f:
                if "AIMAll Professional license check succeeded." in line:
                    self.license_check_succeeded = True
                elif "AIMQB (Version" in line:
                    self.version = Version(line.split()[2])

                # TODO: check these for version 17, because I (YM) am using v 19.
                if self.version.major == 17:

                    if "Wavefunction File:" in line:
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
                    elif "Inp File:" in line:  # AIMAll 19
                        inpfile = Path(line.split()[-1])
                        self[inpfile.stem] = AimAtom(
                            atom=inpfile.stem, inpfile=inpfile
                        )
                    elif "Out File:" in line:  # AIMAll 19
                        outfile = Path(line.split()[-1])
                        self[outfile.stem].outfile = outfile
                    elif "Time Taken" in line:
                        record = line.split()
                        atom, time_taken, integration_error = (
                            record[4],
                            float(record[6]),
                            float(record[8]),
                        )  # todo: check these
                        self[atom].time_taken = time_taken
                        self[atom].integration_error = integration_error

                elif self.version.major == 19:

                    if "Wavefunction File:" in line:
                        self.wfn = Path(line.split()[-1])
                    elif "Number of processors used for this job =" in line:
                        self.nproc = int(line.split()[-1])
                    elif "Number of NACPs  =" in line:
                        self.nacps = int(line.split()[-1])
                    elif "Number of NNACPs =" in line:
                        self.nbacps = int(line.split()[-1])
                    elif "Number of BCPs  =" in line:
                        self.nbcps = int(line.split()[-1])
                    elif "Number of RCPs  =" in line:
                        self.nrcps = int(line.split()[-1])
                    elif "Number of CCPs  =" in line:
                        self.nccps = int(line.split()[-1])

                    if GLOBALS.OPTIMISE_ATOM == "all":

                        # Check which .int files should be produced.
                        # if AIMALL does the partitioning for more than 1 atom, then it does not write out a line with `Out File`
                        if "aimint.exe" in line:
                            aimatom_path = Path(line.split()[-2])
                            # convert the stem to upper, eg. o1 -> O1
                            inpfile = aimatom_path.with_suffix(".inp")
                            outfile = aimatom_path.with_suffix(".int")
                            atom_name = aimatom_path.stem.upper()
                            self[atom_name] = AimAtom(
                                atom=atom, inpfile=inpfile, outfile=outfile
                            )
                        elif "Total time for atom" in line:
                            record = line.split()
                            atom_name = record[4]
                            self[atom_name].time_taken = record[6]
                            self[atom_name].integration_error = record[-1]

                    # if AIMALL only performs partitioning for one atom there are different line in the .aim file
                    else:
                        if "Inp File:" in line:
                            inpfile = Path(line.split()[-1])
                            outfile = inpfile.with_suffix(".int")
                            atom_name = inpfile.stem.upper()
                            self[atom_name] = AimAtom(
                                atom=atom, inpfile=inpfile, outfile=outfile
                            )

                        elif "Total time for atom" in line:
                            record = line.split()
                            atom_name = record[4]
                            self[atom_name].time_taken = record[6]
                            self[atom_name].integration_error = record[-1]

    def __getitem__(self, item: Union[str, int]) -> AimAtom:
        """ If an integer is passed, it returns the atom whose index corresponds to the integer + 1. If a string is passed, it returns
        the the AimAtom which corresponds to the given key."""
        if isinstance(item, int):
            i = item + 1
            for atom, aimatom in self.items():
                if i == get_digits(atom):
                    return aimatom
            raise IndexError(f"No atom with index {item}")
        return super().__getitem__(item)
