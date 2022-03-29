from enum import Enum
from typing import List

class GaussianJobType(Enum):
    """Enum that give variable names to some of the keywords used in a Gaussian job."""

    # this is used to print extra things in the Gaussian output file.
    # since no other job is specified, this defaults to just single point.
    SinglePointEnergy = "p"

    Optimisation = "opt"
    Frequency = "freq"

    @classmethod
    def types(cls) -> List[str]:
        return [ty.value for ty in GaussianJobType]

job_type = GaussianJobType.SinglePointEnergy
startup_options = ["nproc=2", "mem=2gb"]
method = "B3LYP"
basis_set = "6-31+g(d,p)"
charge = 0
multiplicity = 1
keywords = ["nosymm", "output=wfn"]