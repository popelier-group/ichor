from pathlib import Path
from typing import List, Optional, Type, Union

from ichor.core.atoms import Atoms, AtomsNotFoundError
from ichor.core.atoms.alf import ALF
from ichor.core.calculators import default_alf_calculator
from ichor.core.common.dict import merge
from ichor.core.common.functools import classproperty
from ichor.core.common.io import remove
from ichor.core.files.aimall import AIM, INTs
from ichor.core.files.directory import AnnotatedDirectory
from ichor.core.files.file import ReadFile

from ichor.core.files.file_data import HasAtoms, HasProperties, PointDirectoryProperties
from ichor.core.files.gaussian import GaussianOut, GJF, WFN
from ichor.core.files.optional_file import OptionalFile, OptionalPath
from ichor.core.files.pandora import PandoraDirectory, PandoraInput
from ichor.core.files.xyz import XYZ


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
    gaussian_out: OptionalPath[GaussianOut] = OptionalFile
    aim: OptionalPath[AIM] = OptionalFile
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
                    if isinstance(f, WFN):
                        atoms = f.atoms.to_angstroms()
                        self.xyz = XYZ(
                            Path(self.path) / (self.path.name + XYZ.filetype),
                            atoms=atoms,
                        )
                    else:
                        self.xyz = XYZ(
                            Path(self.path) / (self.path.name + XYZ.filetype),
                            atoms=f.atoms,
                        )
                    self.xyz.write()

    @classproperty
    def property_names(self) -> List[str]:
        return INTs.property_names + WFN.property_names

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
        raise AtomsNotFoundError(
            f" {file_with_atoms.__class__.__name__} file does not contain atoms."
        )

    @atoms.setter
    def atoms(self, value: Atoms):
        if value:
            if not self.xyz.exists():
                self.xyz = XYZ(self.path / f"{self.path.name}{XYZ.filetype}")
            self.xyz = XYZ(self.xyz.path, value)
        else:
            raise ValueError(f"Cannot set `atoms` to the given value: {value}.")

    def properties(
        self, system_alf: Optional[List[ALF]] = None
    ) -> PointDirectoryProperties:
        """Get properties contained in the PointDirectory. IF
        no system alf is passed in, an automatic process to get C matrices is started.

        :param system_alf: Optional list of `ALF` instances that can be
            passed in to use a specific alf instead of automatically trying to compute it.
        """

        if not system_alf:
            # TODO: The default alf calculator (the cahn ingold prelog one) should accept
            # connectivity, not connectivity calculator, so connectivity also needs to be passed in.
            system_alf = self.alf(default_alf_calculator)

        c_matrix_dict = self.C_matrix_dict(system_alf)

        # grab properties from WFN
        if self.wfn:
            wfn_properties = self.wfn.properties
        else:
            wfn_properties = {}
        # grab properties from INTs directory
        if self.ints:
            ints_properties = self.ints.properties(c_matrix_dict)
        else:
            ints_properties = {}
        if self.gaussian_out:
            gaussian_output_properties = self.gaussian_out.properties(c_matrix_dict)
        else:
            gaussian_output_properties = {}

        return PointDirectoryProperties(
            merge(wfn_properties, ints_properties, gaussian_output_properties)
        )

    # todo: make this more robust, check for any of the files inside
    @classmethod
    def check_path(cls, path: Path) -> bool:
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
