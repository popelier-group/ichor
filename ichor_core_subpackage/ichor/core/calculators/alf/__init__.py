from typing import Dict, Callable

from ichor.core.calculators.alf.alf import ALF, get_atom_alf
from ichor.core.calculators.alf.cahn_ingold_prelog import \
    calculate_alf_cahn_ingold_prelog
from ichor.core.calculators.alf.sequence import calculate_alf_atom_sequence
    
alf_calculators: Dict[str, Callable] = {
    "cahn_ingold_prelog": calculate_alf_cahn_ingold_prelog,
    "sequence": calculate_alf_atom_sequence,
}

default_alf_calculator: Callable = calculate_alf_cahn_ingold_prelog