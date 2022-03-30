""" natsort is used to sort things like atom names. The code is vendored from the natsort python package (see https://pypi.org/project/natsort/),
but it is made to work in ICHOR without having to download the extra dependency."""

from ichor.common.sorting.natsort import ignore_alpha, natsort
from ichor.common.sorting.natsort.natsort import natsorted


def sort_atoms(atom_list):
    return natsorted(atom_list, key=ignore_alpha)


__all__ = ["natsort", "ignore_alpha", "natsorted", "sort_atoms"]
