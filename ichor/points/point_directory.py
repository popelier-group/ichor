import inspect
import re
from typing import Optional

from ichor.atoms import AtomsNotFoundError
from ichor.common.functools import classproperty
from ichor.files import GJF, WFN, Directory, File, INTs
from ichor.geometry import AtomData
from ichor.points.point import Point


class PointDirectory(Point, Directory):
    """
    A helper class that wraps around ONE directory which contains ONE point (one molecular geometry).

    :param path: Path to a directory which contains ONE point.

    Attributes:
        cls.gjf Optional[GJF]: Used when iterating over __annotations__
        cls.wfn Optional[WFN]: Used when iterating over __annotations__
        cls.ints Optional[INTs]: Used when iterating over __annotations__
    """

    gjf: Optional[GJF] = None
    wfn: Optional[WFN] = None
    ints: Optional[INTs] = None

    def __init__(self, path):
        Directory.__init__(self, path)

    @classproperty
    def dirpattern(self):
        """A regex pattern corresponding to the name of the system name (stored in GLOBALS.SYSTEM_NAME)."""
        from ichor.globals import GLOBALS

        return re.compile(rf"{GLOBALS.SYSTEM_NAME}\d+")

    def parse(self):
        """
        Iterate over __annotations__ which is a dictionary of {"gjf": Optional[GJF], "wfn": Optional[WFN], "ints": Optional[INTs]}
        as defined from class variables in PointsDirectory. Get the type inside the [] brackets. After that it constructs a filetypes
        dictionary containing {"gjf": GJF, "wfn": WFN} and dirtypes dictionary containing {"ints": INTs}
        """
        filetypes = {}
        dirtypes = {}
        for var, type_ in self.__annotations__.items():
            if hasattr(type_, "__args__"):
                type_ = type_.__args__[0]

            # GJF and WFN are subclasses of File
            if issubclass(type_, File):
                filetypes[var] = type_
            # only INTs is a subclass of Directory for now
            elif issubclass(type_, Directory):
                dirtypes[var] = type_

        for f in self:  # calls the __iter__() method which yields pathlib Path objects for all files/folders inside a directory.

            # if the content is a file. This is true for .gjf/.wfn files
            if f.is_file():
                for var, filetype in filetypes.items():
                    # if the suffix is either gjf or wfn, since there could be other files in the directory (such as .gau which we don't use)
                    if f.suffix == filetype.filetype:
                        if (
                            "parent"
                            in inspect.signature(filetype.__init__).parameters
                        ):
                            setattr(self, var, filetype(f, parent=self))
                        else:
                            setattr(self, var, filetype(f))
                        break
            # if the content is a directory. This is currently only for `*_atomicfiles` directories containing .int files
            elif f.is_dir():
                for var, dirtype in dirtypes.items():
                    if dirtype.dirpattern.match(f.name):
                        if (
                            "parent"
                            in inspect.signature(dirtype.__init__).parameters
                        ):
                            # sets the .ints attribute to INTs(path_to_directory, parent=PointDirecotry_instance)
                            setattr(self, var, dirtype(f, parent=self))
                        else:
                            setattr(self, var, dirtype(f))
                        break

    @property
    def atoms(self):
        """Returns the `Atoms` instance which the `PointDirectory` encapsulates."""
        if self.gjf.exists():
            return self.gjf.atoms
        elif self.wfn.exists():
            return self.wfn.atoms
        raise AtomsNotFoundError(f"'atoms' not found for point '{self.path}'")

    def get_atom_data(self, atom) -> AtomData:
        if self.ints:
            return AtomData(self.atoms[atom], self.ints[atom])
        else:
            return AtomData(self.atoms[atom])

    def __getattr__(self, item):
        try:
            return getattr(self.ints, item)
        except AttributeError:
            try:
                return getattr(self.gjf, item)
            except AttributeError:
                try:
                    return getattr(self.wfn, item)
                except AttributeError:
                    raise AttributeError(
                        f"'{self.path}' instance of '{self.__class__.__name__}' object has no attribute '{item}'"
                    )

    def __repr__(self):
        return str(self.path)
