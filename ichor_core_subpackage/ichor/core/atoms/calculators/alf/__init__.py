from typing import Dict, Callable

from ichor.core.atoms.calculators.alf.alf import ALF, get_atom_alf_from_list_of_alfs
from ichor.core.atoms.calculators.alf.cahn_ingold_prelog import \
    calculate_alf_cahn_ingold_prelog
from ichor.core.atoms.calculators.alf.sequence import calculate_alf_atom_sequence
    
alf_calculators: Dict[str, Callable] = {
    "cahn_ingold_prelog": calculate_alf_cahn_ingold_prelog,
    "sequence": calculate_alf_atom_sequence,
}

default_alf_calculator: Callable = calculate_alf_cahn_ingold_prelog