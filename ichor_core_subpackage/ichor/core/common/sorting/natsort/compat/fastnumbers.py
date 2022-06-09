# -*- coding: utf-8 -*-
"""
Interface for natsort to access fastnumbers functions without
having to worry if it is actually installed.
"""

from distutils.version import StrictVersion

# If the user has fastnumbers installed, they will get great speed
# benefits. If not, we use the simulated functions that come with natsort.
try:
    # noinspection PyPackageRequirements
    from fastnumbers import __version__ as fn_ver
    from fastnumbers import fast_float, fast_int

    # Require >= version 2.0.0.
    if StrictVersion(fn_ver) < StrictVersion("2.0.0"):
        raise ImportError  # pragma: no cover
except ImportError:
    from .fake_fastnumbers import fast_float, fast_int  # noqa: F401
