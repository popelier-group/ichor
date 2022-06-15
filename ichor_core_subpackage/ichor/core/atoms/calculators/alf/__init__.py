from typing import Dict

from ichor.core.atoms.calculators.alf.alf import ALF, ALFCalculatorFunction
from ichor.core.atoms.calculators.alf.cahn_ingold_prelog import \
    calculate_alf_cahn_ingold_prelog
from ichor.core.atoms.calculators.alf.sequence import \
    calculate_alf_atom_sequence

alf_calculators: Dict[str, ALFCalculatorFunction] = {
    "cahn_ingold_prelog": calculate_alf_cahn_ingold_prelog,
    "sequence": calculate_alf_atom_sequence,
}

default_alf_calculator: ALFCalculatorFunction = alf_calculators[
    "cahn_ingold_prelog"
]
