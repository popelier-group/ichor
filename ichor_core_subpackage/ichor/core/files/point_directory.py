from pathlib import Path
from typing import Union

from ichor.core.atoms import Atoms, AtomsNotFoundError
from ichor.core.files import OrcaInput, OrcaOutput
from ichor.core.files.aimall import Aim, IntDirectory
from ichor.core.files.directory import AnnotatedDirectory
from ichor.core.files.file_data import HasAtoms, HasData
from ichor.core.files.gaussian import GaussianOutput, GJF, WFN
from ichor.core.files.pandora import PandoraDirectory, PandoraInput
from ichor.core.files.xyz import XYZ


class PointDirectory(AnnotatedDirectory, HasAtoms, HasData):
    """
    A helper class that wraps around ONE directory which contains ONE point (one molecular geometry).

    :param path: Path to a directory which contains ONE point.
    """

    _suffix = ".pointdir"

    contents = {
        "xyz": XYZ,
        "gjf": GJF,
        "gaussian_output": GaussianOutput,
        "orca_input": OrcaInput,
        "orca_output": OrcaOutput,
        "aim": Aim,
        "wfn": WFN,
        "ints": IntDirectory,
        "pandora_input": PandoraInput,
        "pandora_directory": PandoraDirectory,
    }

    def __init__(self, path: Union[Path, str]):
        AnnotatedDirectory.__init__(self, path)

    @classmethod
    def check_path(cls, path: Path) -> bool:
        """Makes sure that path is PointDirectory-like"""
        return (path.suffix == cls._suffix) and path.is_dir()

    @property
    def raw_data(self) -> dict:

        all_data = {}

        for attr_name in self.contents.keys():
            # all contents which subclass from HasData should have raw_data attribute implemented
            attr = getattr(self, attr_name)
            if isinstance(attr, HasData):
                d = attr.raw_data
                all_data[attr_name] = d

        return all_data

    @property
    def atoms(self) -> Atoms:
        """Returns the `Atoms` instance which the `PointDirectory` encapsulates."""

        # we should always have an xyz file, so just return the atoms from there
        # this is likely the best solution, so that we always know what is returned
        # and will error out if an xyz is not present
        if self.xyz:
            return self.xyz.atoms

        raise FileNotFoundError(
            f"There is no .xyz file in the current {self.__class__.__name__} instance: {self.path.absolute()}"
        )

    def atoms_from_file(self, file_with_atoms: HasAtoms) -> Atoms:
        """Given a class (which is in the contents of the directory), obtain
        the Atoms instance from that specific file which is wrapped by the class.

        :param file_with_atoms: file class which subclasses from HasAtoms
            and has a ``.atoms`` attribute
        :raises AtomsNotFoundError: If file class does not contain atoms
        :return: _description_
        :rtype: Atoms
        """
        for f in self.files:
            # try to return atoms
            if isinstance(f, file_with_atoms):
                try:
                    return f.atoms
                # if for some reason the given file does not have atoms attribute
                except AttributeError:
                    raise AtomsNotFoundError(
                        f" {file_with_atoms.__class__.__name__} file does not contain atoms."
                    )

    @atoms.setter
    def atoms(self, atms: Atoms):
        """Overwrites the current .xyz file with the atoms info that is passed in.

        :param atms: An atoms instance containing geometry information
        """
        if atms:
            if not self.xyz.exists():
                self.xyz = XYZ(self.path / f"{self.path.name}{XYZ.filetype}")
            self.xyz = XYZ(self.xyz.path, atms)

    def __repr__(self):
        """Returns string representation, including class name and path"""
        return self.__class__.__name__ + f'"{str(self.path)}"'
