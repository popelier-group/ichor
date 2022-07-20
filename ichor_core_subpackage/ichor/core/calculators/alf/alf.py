
from typing import NamedTuple, Optional, List, Union


class ALF(NamedTuple):
    """Atomic Local Frame used for one atom. Atomic local frame consists of central atom index,
    x-axis atom index, xy-plane atom index. These indices are 0-indexed. The xy-plane atom
    might not exist if there are only 2 atoms, so default for it is None."""

    origin_idx: int
    x_axis_idx: int
    xy_plane_idx: Optional[int] = None

def get_atom_alf(atom: "Atom", alf: Union[ALF, List[ALF]]):
    
    if isinstance(alf, ALF):
        if alf.origin_idx != atom.i:
            raise ValueError(f"The passed ALF origin index {alf.origin_idx} does not match atom index {atom.i} (0-indexed).")
        return alf
    else:
        alf_found = False
        for a in alf:
            if a.origin_idx == atom.i:
                return a
        
        if not alf_found:
            raise ValueError(f"The list of ALFs does not contain the alf of the atom with index {atom.i}")