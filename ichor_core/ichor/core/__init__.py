# TODO: removing this causes cyclic imports
# fix these cyclic imports in future versions
# since this is here, types is imported first which is why no
# cyclic imports are seen...
from ichor.core.common.types import Version  # noqa: F401

# The packaging version, which setuptools reads through `version = attr:` in
# setup.cfg. Kept as a plain string literal so that it can be parsed without
# importing ichor.core at build time, when its dependencies are not installed yet.
#
# This only ever increases, so that pip, the git tags and any published artifacts
# stay in order. It is not the number ICHOR is published under -- see ICHOR_RELEASE.
__version__ = "5.0.0"

# The iteration of ICHOR that this is, as it is referred to in the literature.
# The 2022 paper is plain ICHOR; this rewrite is published as its follow up, so
# it is ICHOR v2.0 no matter what the packaging version happens to be.
#
# The two are deliberately separate. __version__ was already past 4 by the time this
# rewrite was named, and packaging versions are not allowed to go backwards, so one
# number cannot do both jobs. When the next iteration is published, this becomes
# "ICHOR v3.0" and __version__ takes its next major bump.
ICHOR_RELEASE = "ICHOR v2.0"
