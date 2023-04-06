"""Atomic Local Frame used for one atom. Atomic local frame consists of central atom index,
x-axis atom index, xy-plane atom index. These indices are 0-indexed. The xy-plane atom
might not exist if there are only 2 atoms, so default for it is None."""

from collections import namedtuple

# default for xy_plane_idx is None as a molecule can have 2 atoms only (e.g. HCl)
ALF = namedtuple("ALF", "origin_idx x_axis_idx xy_plane_idx", defaults=(None,))
