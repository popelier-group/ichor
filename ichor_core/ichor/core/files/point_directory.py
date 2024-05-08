from pathlib import Path
from typing import Callable, Union

from ichor.core.atoms import Atoms, AtomsNotFoundError
from ichor.core.files import OrcaInput, OrcaOutput
from ichor.core.files.aimall import Aim, IntDirectory
from ichor.core.files.directory import AnnotatedDirectory
from ichor.core.files.file_data import HasAtoms, HasData
from ichor.core.files.gaussian import GaussianOutput, GJF, WFN
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
            # this also automatically checks for OptionalContent
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
        elif self.wfn:
            return self.wfn.atoms.to_angstroms()

        raise FileNotFoundError(
            f"There is no .xyz or .wfn file in the current {self.__class__.__name__} instance: {self.path.absolute()}"
        )

    def atoms_from_file(self, file_with_atoms: HasAtoms) -> Atoms:
        """Given a class (which is in the contents of the directory), obtain
        the Atoms instance from that specific file which is wrapped by the class.

        :param file_with_atoms: file class which subclasses from HasAtoms
            and has a ``.atoms`` attribute
        :raises ichor.core.atoms.AtomsNotFoundError: If file class does not contain atoms
        :return: _description_
        :rtype: ichor.core.atoms.Atoms
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

    def features(
        self,
        feature_calculator: Callable,
        *args,
        is_atomic=True,
        **kwargs,
    ):
        """Returns the features for this Atoms instance,
        corresponding to the features of each Atom instance held in this Atoms isinstance
        Features are calculated in the Atom class and concatenated to a 2d array here.

        The array shape is n_atoms x n_features (3*n_atoms - 6)

        :param is_atomic: whether the feature calculator calculates features
            for individual atoms or for the whole geometry.
        :param args: positional arguments to pass to feature calculator
        :param kwargs: key word arguments to pass to feature calculator

        Returns:
            :type: `np.ndarray` of shape n_atoms x n_features (3N-6)
                Return the feature matrix of this Atoms instance
        """
        return self.atoms.features(
            feature_calculator, *args, is_atomic=is_atomic, **kwargs
        )

    @atoms.setter
    def atoms(self, atms: Atoms):
        """Overwrites the current .xyz file with the atoms info that is passed in.

        :param atms: An atoms instance containing geometry information
        """
        if atms:
            if not self.xyz.exists():
                self.xyz = XYZ(self.path / f"{self.path.name}{XYZ.get_filetype()}")
            self.xyz = XYZ(self.xyz.path, atms)

    def __repr__(self):
        """Returns string representation, including class name and path"""
        return self.__class__.__name__ + f'"{str(self.path)}"'
