from ast import Call
from ctypes import Union
from re import L
from typing import NamedTuple, Optional
from typing import List, Callable


class ALF(NamedTuple):
    """Atomic Local Frame used for one atom. Atomic local frame consists of central atom index,
    x-axis atom index, xy-plane atom index. These indices are 0-indexed. The xy-plane atom
    might not exist if there are only 2 atoms, so default for it is None."""

    origin_idx: int
    x_axis_idx: int
    xy_plane_idx: Optional[int] = None

def get_atom_alf_from_list_of_alfs(alf: List[ALF], atom_instance: "Atom") -> ALF:
    for atom_alf in alf:
        if atom_alf.origin_idx == atom_instance.i:
            return atom_alf
    raise IndexError(f"No index '{atom_instance.i}' in ALF: '{alf}'")