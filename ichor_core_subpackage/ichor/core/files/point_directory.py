from pathlib import Path
from typing import List, Optional, Type, Union

from ichor.core.atoms import Atoms, AtomsNotFoundError
from ichor.core.atoms.alf import ALF
from ichor.core.calculators import default_alf_calculator
from ichor.core.common.dict import merge
from ichor.core.files import OrcaInput, OrcaOutput
from ichor.core.files.aimall import AIM, INTs
from ichor.core.files.directory import AnnotatedDirectory

from ichor.core.files.file_data import HasAtoms, HasData, PointDirectoryProperties
from ichor.core.files.gaussian import GaussianOutput, GJF, WFN
from ichor.core.files.pandora import PandoraDirectory, PandoraInput
from ichor.core.files.xyz import XYZ


class PointDirectory(HasAtoms, HasData, AnnotatedDirectory):
    """
    A helper class that wraps around ONE directory which contains ONE point (one molecular geometry).

    :param path: Path to a directory which contains ONE point.
    """

    def __init__(self, path: Union[Path, str]):
        AnnotatedDirectory.__init__(self, path)

    @classmethod
    def check_path(cls, path: Path) -> bool:
        """Makes sure the path exists and is a directory."""
        return path.exists() and path.is_dir()

    def _contents(self):
        """
        Inner contents of the directory. The keys of this dictionary will be accessible as attributes
        and the values (the classes) are going to be used to parse the files.
        """

        return {
            "xyz": XYZ,
            "gaussian_input": GJF,
            "gaussian_output": GaussianOutput,
            "orca_input": OrcaInput,
            "orca_output": OrcaOutput,
            "aim": AIM,
            "wfn": WFN,
            "ints": INTs,
            "pandora_input": PandoraInput,
            "pandora_directory": PandoraDirectory,
        }

    @property
    def raw_data(self) -> List[str]:
        # TODO: implement this so that it returns
        return INTs.property_names + WFN.property_names

    # TODO: implement processed_data
    def processed_data(self, params_for_processing: dict):
        """Pass in a dictionary with keys: Python classes (of files/directories, eg. GJF, INTs)
          for which processing needs to be done, and values: a dictionary containing

        :param params_for_processing: _description_
        :type params_for_processing: dict
        :raises FileNotFoundError: _description_
        :raises AtomsNotFoundError: _description_
        :return: _description_
        :rtype: _type_
        """

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

        # possibly remove these priorities as XYZ should always exist in the directory.
        # if .xyz does not exist, then .atoms attribute might not exist as well
        # so there would be no need to subclass from HasAtoms, but that depends on what you use the code for

        # always try to get atoms from wfn file first because the wfn file contains the final geometry.
        # you can run into the issue where you did an optimization (so .xyz/gjf are different from wfn)
        # then predictions - true will be way off because you are predicting on different geometries

        # file_priorities = [XYZ, WFN, GJF]

        # for f in file_priorities:
        #     for f_inst in self.files():
        #         if isinstance(f_inst, f):
        #             return f_inst.atoms

        # # in case file priorities does not have the class
        # for f in self.files():
        #     if isinstance(f, HasAtoms):
        #         return f.atoms

        # raise AtomsNotFoundError(f"'atoms' not found for point '{self.path}'")

    def atoms_from_file(self, file_with_atoms: Type[HasAtoms]) -> Atoms:
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

    # TODO: move to processed_data
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

    def __repr__(self):
        return str(self.path)
