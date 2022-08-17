from pathlib import Path
from typing import Optional, Union

from ichor.core.common.functools import classproperty
from ichor.core.common.str import get_digits
from ichor.core.common.types import Version
from ichor.core.files import File, ReadFile, FileContents


class AimAtom:
    """Helper class which stores information for each atom which was in the
    AIMAll output file. Information such as timing required to integrate atom,
    as well as the integration error are stored."""

    def __init__(
        self,
        atom_name: Optional[str] = None,
        inp_file: Optional[Path] = None,
        int_file: Optional[Path] = None,
        time_taken: Optional[int] = None,
        integration_error: Optional[float] = None,
    ):
        self.atom_name = atom_name
        self.inp_file = inp_file
        self.int_file = int_file
        self.time_taken = time_taken
        self.integration_error = integration_error


class AIM(ReadFile, File, dict):
    """Class which wraps around an AIMAll output file, where settings and timings are
    written out to. The .int files are parsed separately in the INT/INTs classes."""

    def __init__(
        self,
        path: Path,
        license_check_succeeded: Optional[bool] = FileContents,
        version: Version = FileContents,
        wfn_path: Path = FileContents,
        extout_path: Optional[Path] = FileContents,
        mgp_path: Optional[Path] = FileContents,
        sum_path: Optional[Path] = FileContents,
        sumviz_path: Optional[Path] = FileContents,
        nproc: int = FileContents,
        nacps: int = FileContents,
        nnacps: int = FileContents,
        nbcps: int = FileContents,
        nrcps: int = FileContents,
        nccps: int = FileContents,
        output_file: Path = FileContents,
        cwd: Path = FileContents,
    ):
        File.__init__(self, path)
        dict.__init__(self)

        self.license_check_succeeded = license_check_succeeded
        self.version = version
        self.wfn_path = wfn_path
        self.extout_path = extout_path
        self.mgp_path = mgp_path
        self.sum_path = sum_path
        self.sumviz_path = sumviz_path
        self.nproc = nproc
        self.nacps = nacps
        self.nnacps = nnacps
        self.nbcps = nbcps
        self.nrcps = nrcps
        self.nccps = nccps
        self.output_file = output_file
        self.cwd = cwd

    @classproperty
    def filetype(self) -> str:
        """Returns the file suffix associated with AIMAll output files"""
        return ".aim"

    def _read_file(self):
        """Reads in AIMAll output file that contains information about the calculation.

        .. note::
            This file does not contain IQA energies or multipole moments. That information is stored
            in .int files (so use the INT class to parse).
        """

        self.license_check_succeeded = False

        with open(self.path, "r") as f:

            lines = f.readlines()
            is_all_atom_calculation = any(
                "aimint.exe" in line for line in lines
            )
            for line in lines:

                # need this to use multiple cores for systems above certain number of atoms (see AIMAll manual)
                if "AIMAll Professional license check succeeded." in line:
                    self.license_check_succeeded = True
                elif "AIMQB (Version" in line:
                    self.version = Version(line.split()[2])
                elif "Wavefunction File:" in line:
                    self.wfn_path = Path(line.split()[-1])
                elif "Number of processors used for this job =" in line:
                    self.nproc = int(line.split()[-1])
                elif "Number of NACPs  =" in line:
                    self.nacps = int(line.split()[-1])
                elif "Number of NNACPs =" in line:
                    self.nnacps = int(line.split()[-1])
                elif "Number of BCPs  =" in line:
                    self.nbcps = int(line.split()[-1])
                elif "Number of RCPs  =" in line:
                    self.nrcps = int(line.split()[-1])
                elif "Number of CCPs  =" in line:
                    self.nccps = int(line.split()[-1])

                if is_all_atom_calculation and "aimint.exe" in line:
                    # find the path to where the atom information will be stored (this is without suffix), also remove extra " in line
                    aimatom_path = Path(line.split()[-2].strip('"'))
                    # convert the stem to upper, eg. o1 -> O1
                    inpfile = aimatom_path.with_suffix(".inp")
                    outfile = aimatom_path.with_suffix(".int")
                    atom_name = aimatom_path.stem.capitalize()
                    self[atom_name] = AimAtom(
                        atom_name=atom_name,
                        inp_file=inpfile,
                        int_file=outfile,
                    )
                elif (
                    is_all_atom_calculation
                    and "Total time for atom" in line
                    or not is_all_atom_calculation
                    and "Inp File:" not in line
                    and "Total time for atom" in line
                ):
                    record = line.split()
                    atom_name = record[4].capitalize()
                    self[atom_name].time_taken = int(record[6])
                    self[atom_name].integration_error = float(record[-1])

                elif not is_all_atom_calculation and "Inp File:" in line:
                    inpfile = Path(line.split()[-1].strip('"'))
                    outfile = inpfile.with_suffix(".int")
                    atom_name = inpfile.stem.capitalize()
                    self[atom_name] = AimAtom(
                        atom_name=atom_name,
                        inp_file=inpfile,
                        int_file=outfile,
                    )

    def __getitem__(self, item: Union[str, int]) -> AimAtom:
        """If an integer is passed, it returns the atom whose index corresponds to the integer (indexing starts at 1).
        If a string is passed, it returns the the AimAtom which corresponds to the given key."""
        if isinstance(item, int):
            for atom_name, aimatom in self.items():
                if item == get_digits(atom_name):
                    return aimatom
            raise IndexError(f"No atom with index {item}")
        elif isinstance(item, str):
            item = item.capitalize()
            return super().__getitem__(item)
        else:
            raise NotImplementedError(
                f"__getitem__ expects a str or int. Currently type is {type(item)}"
            )
