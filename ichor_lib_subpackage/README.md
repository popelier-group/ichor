# ICHOR Library

This is the library package, containing classes and functions which read specific files (such as gjfs, ints, xyzs, etc.) that make it easier to manage and modify files.

## Installation

If installing from source code (i.e. the repository has been cloned locally) do

```
python -m pip install ichor_lib_subpackage/
```

You can also install from wheel file (download from release tab)

```python -m pip install 
ichor_lib-3.0.0-py37-none-any.whl
```

## Usage
When you have installed the library portion of ichor, you can import is like so

```
import ichor.ichor_lib
```

To import specific modules, you can do

```
from ichor.ichor_lib import atoms

atoms_instance = atoms.Atoms()
```

Because the `__init__.py` files in the subpackages (directories containing modules) have some classes imported already, you can do

```
from ichor.ichor_lib.atoms import Atoms
from ichor.ichor_lib.files import WFN, GJF, XYZ

atoms_instance = Atoms()
```