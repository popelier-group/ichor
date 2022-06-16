from typing import NamedTuple, Optional
from typing_extensions import Protocol


class ALF(NamedTuple):
    """Atomic Local Frame used for one atom. Atomic local frame consists of central atom index,
    x-axis atom index, xy-plane atom index. These indices are 0-indexed. The xy-plane atom
    might not exist if there are only 2 atoms, so default for it is None."""

    origin_idx: int
    x_axis_idx: int
    xy_plane_idx: Optional[int] = None


class ALFCalculatorFunction(Protocol):
    def __call__(self, atom: "Atom", *args, **kwargs) -> ALF:
        ...
