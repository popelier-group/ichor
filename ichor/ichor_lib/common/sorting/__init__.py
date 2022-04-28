""" natsort is used to sort things like atom names. The code is vendored from the natsort python package (see https://pypi.org/project/natsort/),
but it is made to work in ICHOR without having to download the extra dependency."""

from ichor.ichor_lib.common.sorting.natsort import ignore_alpha, natsort

__all__ = ["natsort", "ignore_alpha"]
