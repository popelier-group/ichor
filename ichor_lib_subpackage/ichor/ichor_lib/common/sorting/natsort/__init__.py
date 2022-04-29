# -*- coding: utf-8 -*-

import re

from .natsort import (as_ascii, as_utf8, decoder, humansorted,
                      index_humansorted, index_natsorted, index_realsorted,
                      natsort_key, natsort_keygen, natsorted, ns,
                      numeric_regex_chooser, order_by_index, os_sort_key,
                      os_sort_keygen, os_sorted, realsorted)
from .utils import chain_functions

__version__ = "7.1.1"


int_finder = re.compile(rf"(\D+)({numeric_regex_chooser(ns.INT | ns.SIGNED)})")


def get_int(matchobj):
    return matchobj.group(2)


def ignore_alpha(x):
    return int_finder.sub(get_int, str(x))


__all__ = [
    "natsort_key",
    "natsort_keygen",
    "natsorted",
    "humansorted",
    "realsorted",
    "index_natsorted",
    "index_humansorted",
    "index_realsorted",
    "order_by_index",
    "decoder",
    "as_ascii",
    "as_utf8",
    "ns",
    "chain_functions",
    "numeric_regex_chooser",
    "os_sort_key",
    "os_sort_keygen",
    "os_sorted",
    "ignore_alpha",
]

# Add the ns keys to this namespace for convenience.
globals().update(ns._asdict())
