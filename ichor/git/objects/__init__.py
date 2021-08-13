"""
Import all submodules main classes into the package space
"""
# flake8: noqa
import inspect

from ichor.git.objects.base import *
from ichor.git.objects.blob import *
from ichor.git.objects.commit import *
from ichor.git.objects.submodule import util as smutil
from ichor.git.objects.submodule.base import *
from ichor.git.objects.submodule.root import *
from ichor.git.objects.tag import *
from ichor.git.objects.tree import *
# Fix import dependency - add IndexObject to the util module, so that it can be
# imported by the submodule.base
smutil.IndexObject = IndexObject  # type: ignore[attr-defined]
smutil.Object = Object  # type: ignore[attr-defined]
del(smutil)

# must come after submodule was made available

__all__ = [name for name, obj in locals().items()
           if not (name.startswith('_') or inspect.ismodule(obj))]
