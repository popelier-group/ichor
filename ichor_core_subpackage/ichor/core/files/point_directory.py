from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

from ichor.core.atoms import Atoms, AtomsNotFoundError
from ichor.core.atoms.alf import ALF
from ichor.core.calculators import default_alf_calculator
from ichor.core.common.dict import merge
from ichor.core.files import OrcaInput, OrcaOutput
from ichor.core.files.aimall import Aim, IntDirectory
from ichor.core.files.directory import AnnotatedDirectory

from ichor.core.files.file_data import HasAtoms, HasData
from ichor.core.files.gaussian import GaussianOutput, GJF, WFN
from ichor.core.files.pandora import PandoraDirectory, PandoraInput
from ichor.core.files.xyz import XYZ


class PointDirectory(HasAtoms, HasData, AnnotatedDirectory):
    """
    A helper class that wraps around ONE directory which contains ONE point (one molecular geometry).

    :param path: Path to a directory which contains ONE point.
    """

    contents = {
        "xyz": XYZ,
        "gaussian_input": GJF,
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
        """Makes sure the path exists and is a directory."""
        return path.exists() and path.is_dir()

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

    # TODO: implement processed_data
    def processed_data(self, processing_instructions: Dict[HasData, Callable]):
        """Pass in a dictionary with keys: Python classes (of files/directories, eg. GJF, INTs)
        and values being functions (could also be lambda functions)
        which tell how to process the data that is found in the instance of the given class.

        return a dictionary of key: attribute name as a string, and value: a dictionary
        containing the processed data for that file/directory
        """

        # check that data can actually be obtained for the classes that are given
        for cls in processing_instructions.keys():
            if not issubclass(cls, HasData):
                raise ValueError(f"The class {cls.__name__} does not contain data.")

        all_processed_data = {}

        # inverse the class to str from self.contents
        cls_to_attr_name_dict = self.type_to_contents

        # loop over the classes we want to get data for
        # they might only be a few of the many files we have in the directory
        for cls in processing_instructions.keys():
            # get the instance of that specific class that is held inside the PointDirectory
            attr_as_str = cls_to_attr_name_dict.get(cls)
            # if the attribute does not exist for some reason, maybe the wrong class is given
            if not attr_as_str:
                raise ValueError(
                    f"The type of file is not found in the instance of {self.__class__.__name__}."
                )

            # we checked all classes have data before, so no need to check again
            obj_with_data = getattr(self, attr_as_str)
            # check if the object actually exists, because it might not be present on disk
            if obj_with_data:
                processed_data = obj_with_data.processed_data(
                    processing_instructions[cls]
                )
                all_processed_data[attr_as_str] = processed_data

        return all_processed_data

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

    # TODO: move to processed_data
    def properties(self, system_alf: Optional[List[ALF]] = None):
        """Get properties contained in the PointDirectory. IF
        no system alf is passed in, an automatic process to get C matrices is started.

        :param system_alf: Optional list of `ALF` instances that can be
            passed in to use a specific alf instead of automatically trying to compute it.
        """

        # TODO: remove this automatic things, everything automatic should be in data_processing package

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

        return merge(wfn_properties, ints_properties, gaussian_output_properties)

    def __repr__(self):
        """Returns string representation, including class name and path"""
        return self.__class__.__name__ + f'"{str(self.path)}"'
