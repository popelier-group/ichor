from ichor.core.common.types import Version

# TODO: removing this causes cyclic imports
# fix these cyclic imports in future versions
# since this is here, types is imported first which is why no
# cyclic imports are seen...
__version__ = Version("4.0.3")
