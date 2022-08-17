from typing import Dict, Callable, Union, List

from ichor.core.calculators.alf.cahn_ingold_prelog_alf_calculator import \
    calculate_alf_cahn_ingold_prelog
from ichor.core.calculators.alf.sequence_alf_calculator import calculate_alf_atom_sequence
    
alf_calculators: Dict[str, Callable] = {
    "cahn_ingold_prelog": calculate_alf_cahn_ingold_prelog,
    "sequence": calculate_alf_atom_sequence,
}

default_alf_calculator: Callable = calculate_alf_atom_sequence

def get_atom_alf(atom: "Atom", alf: Union["ALF", List["ALF"], Dict[str, "ALF"]]):
    
    from ichor.core.atoms.alf import ALF
    
    if isinstance(alf, ALF):
        if alf.origin_idx != atom.i:
            raise ValueError(f"The passed ALF origin index {alf.origin_idx} does not match atom index {atom.i} (0-indexed).")
        return alf
    
    elif isinstance(alf, dict):
        for atom_name, a in alf.items():
            if a[0] == atom.i:
                return a
    
    else:
        alf_found = False
        for a in alf:
            if a[0] == atom.i:
                return a
        
        if not alf_found:
            raise ValueError(f"The list of ALFs does not contain the alf of the atom with index {atom.i}")
        
    raise NotImplementedError("Can only give an instance of `ALF` or list of `ALF`.")