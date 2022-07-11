from pathlib import Path
from typing import Union, Dict, Any, Optional, Type

from ichor.core.atoms import AtomsNotFoundError, Atoms
from ichor.core.files.directory import AnnotatedDirectory
from ichor.core.files.file import FileContents, ReadFile

import numpy as np

from ichor.core.files.file_data import HasAtoms, HasProperties, AtomicData
from ichor.core.files.gjf import GJF
from ichor.core.files.ints import INTs
from ichor.core.files.optional_file import OptionalFile, OptionalPath
from ichor.core.files.pandora import PandoraDirectory, PandoraInput
from ichor.core.files.wfn import WFN
from ichor.core.files.xyz import XYZ
from ichor.core.common.dict import merge
from ichor.core.common.functools import classproperty
from ichor.core.common.io import remove
from ichor.core.atoms.calculators.features.features import FeatureCalculatorFunction


class PointDirectory(HasAtoms, HasProperties, AnnotatedDirectory):
    """
    A helper class that wraps around ONE directory which contains ONE point (one molecular geometry).

    :param path: Path to a directory which contains ONE point.

    Attributes:
        cls.gjf Optional[GJF]: Used when iterating over __annotations__
        cls.wfn Optional[WFN]: Used when iterating over __annotations__
        cls.ints Optional[INTs]: Used when iterating over __annotations__
    """

    xyz: OptionalPath[XYZ] = OptionalFile
    gjf: OptionalPath[GJF] = OptionalFile
    wfn: OptionalPath[WFN] = OptionalFile
    ints: OptionalPath[INTs] = OptionalFile
    pandora_input: OptionalPath[PandoraInput] = OptionalFile
    pandora: OptionalPath[PandoraDirectory] = OptionalFile

    def __init__(self, path: Union[Path, str]):
        AnnotatedDirectory.__init__(self, path)

    def _read_file(self, *args, **kwargs):
        for f in self.path_objects():
            if isinstance(f, ReadFile):
                f.read(*args, **kwargs)

    def _parse(self):
        super()._parse()  # call AnnotatedDirectory.parse method
        if not self.xyz:
            for f in self.files():
                if isinstance(f, HasAtoms):
                    self.xyz = XYZ(
                        Path(self.path) / (self.path.name + XYZ.filetype),
                        atoms=f.atoms,
                    )
        for p in self.path_objects():
            if hasattr(p, "parent"):
                p.parent = self

            if hasattr(p, "wfn") and self.wfn.exists():
                p.wfn = self.wfn

    @property
    def atoms(self) -> Atoms:
        """Returns the `Atoms` instance which the `PointDirectory` encapsulates."""
        # always try to get atoms from wfn file first because the wfn file contains the final geometry.
        # you can run into the issue where you did an optimization (so .xyz/gjf are different from wfn)
        # then predictions - true will be way off because you are predicting on different geometries

        file_priorities = [XYZ, WFN, GJF]

        for f in file_priorities:
            for f_inst in self.files():
                if isinstance(f_inst, f):
                    return f_inst.atoms

        # in case file priorities does not have the class
        for f in self.files():
            if isinstance(f, HasAtoms):
                return f.atoms

        raise AtomsNotFoundError(f"'atoms' not found for point '{self.path}'")

    def atoms_from_file(self, file_with_atoms: Type[HasAtoms]) -> Atoms:
        for f in self.files():
            if isinstance(f, file_with_atoms):
                return f.atoms
        raise AtomsNotFoundError(f" {file_with_atoms.__class__.__name__} file does not contain atoms.")

    @atoms.setter
    def atoms(self, value: Atoms):
        if value is not FileContents:
            if not self.xyz.exists():
                self.xyz = XYZ(self.path / f"{self.path.name}{XYZ.filetype}")
            self.xyz = XYZ(self.xyz.path, value)

    @property
    def features_file(self) -> Path:
        return self.path / (self.path.name + ".features")

    def get_atom_data(self, atom_name) -> AtomicData:
        return AtomicData(self.atoms[atom_name], self.properties)

    @property
    def properties(self) -> Dict[str, Any]:
        return merge(
            *[
                f.properties
                for f in self.path_objects()
                if isinstance(f, HasProperties)
            ]
        )

    @classmethod
    def check_path(
        cls, path: Path
    ) -> bool:  # todo: make this more robust, check for any of the files inside
        return path.exists() and path.is_dir()

    @classproperty
    def ignore_file_stem(self) -> Path:
        return Path("ignore")

    @property
    def ignore_file(self) -> Path:
        return self.path / PointDirectory.ignore_file_stem

    @property
    def should_ignore(self) -> bool:
        return self.ignore_file.exists()

    def ignore(self, reason: Optional[str] = None):
        with open(self.ignore_file, "a") as f:
            if reason is not None:
                f.write(reason)

    def stop_ignore(self):
        if self.ignore_file.exists():
            remove(self.ignore_file)

    def __repr__(self):
        return str(self.path)

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.get_atom_data(item)
        return super().__getitem__(item)
