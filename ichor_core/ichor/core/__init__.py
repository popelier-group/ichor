# TODO: removing this causes cyclic imports
# fix these cyclic imports in future versions
# since this is here, types is imported first which is why no
# cyclic imports are seen...
from ichor.core.common.types import Version  # noqa: F401

# Kept as a plain string literal so that setuptools can read it statically for
# `version = attr: ichor.core.__version__` in setup.cfg. Wrapping it in `Version`
# would force setuptools to import ichor.core at build time, when the
# dependencies it imports are not installed yet.
__version__ = "4.0.3"
