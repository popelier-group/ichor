from enum import Enum
from typing import List
from pathlib import Path

class GaussianJobType(Enum):
    """Enum that give variable names to some of the keywords used in a Gaussian job."""

    # this is used to print extra things in the Gaussian output file.
    # since no other job is specified, this defaults to just single point.
    Optimisation = "opt"
    Frequency = "freq"
    SinglePoint = ""

    @classmethod
    def types(cls) -> List[str]:
        return [ty.value for ty in GaussianJobType]

def extra_details_str_fnc(path: Path):

    return f"\n{path.with_suffix('.wfn').name}\n"


job_type = GaussianJobType.SinglePoint
startup_options = []
method = "B3LYP"
basis_set = "6-31+g(d,p)"
charge = 0
multiplicity = 1
keywords = ["nosymm", "output=wfn"]