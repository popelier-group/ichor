from typing import Dict

from ichor.core.atoms import ALF
from ichor.core.calculators import default_alf_calculator
from ichor.core.processing.callables import (
    fflux_gaussian_output_processing_function,
    fflux_ints_directory_processing_function,
)


def fflux_point_directory_processing(
    alf_dict: Dict[str, ALF] = None, central_atom_name: str = None
):

    # commented code was to automatically detect function, did not work well
    # processing_dict = {
    #     WFN: no_processing_function,
    #     IntDirectory: fflux_ints_directory_processing_function,
    #     GaussianOutput: fflux_gaussian_output_processing_function
    # }

    # check that data can actually be obtained for the classes that are given
    # for cls in processing_dict.keys():
    #     if not issubclass(cls, HasData):
    #         raise ValueError(f"The class {cls.__name__} does not contain data.")
    # default alf if not given

    def _processing_func(point_directory):

        # use the nonlocal variables here because otherwise it gives an error
        # because it will think that the local variable, e.g. "alf_dict"
        # is referenced before assignment, because it sees that the **local**
        # "alf_dict" variable is assigned later.
        # i.e. we need to access the nonlocal variable
        nonlocal alf_dict
        nonlocal central_atom_name

        if not alf_dict:
            alf_dict = point_directory.alf_dict(default_alf_calculator)

        central_atom_name_given = True
        # set central atom as first atom found
        if not central_atom_name:
            central_atom_name_given = False
            central_atom_name = point_directory.atoms[0].name

        # c matrix dictionary needed to rotate multipole moments
        c_matrix_dict = point_directory.C_matrix_dict(alf_dict)
        # use the central atom c matrix to rotate forces for that atom
        central_atom_c_matrix = c_matrix_dict[central_atom_name]

        # the final dictionary that will be returned
        all_processed_data = {}

        all_processed_data["wfn"] = point_directory.wfn.raw_data
        all_processed_data["ints"] = point_directory.ints.processed_data(
            fflux_ints_directory_processing_function(c_matrix_dict)
        )

        if central_atom_name_given:
            all_processed_data[
                "gaussian_output"
            ] = point_directory.gaussian_out.processed_data(
                fflux_gaussian_output_processing_function(central_atom_c_matrix)
            )

        return all_processed_data

    return _processing_func

    # TODO: below code was to automatically determine what function to use for each class
    # TODO: however there isn't a nice way to pass parameters to the functions then.

    # # inverse the key,value, so it is class:attr_name from self.contents
    # cls_to_attr_name_dict = point_directory.type_to_contents

    # # loop over the classes we want to get data for
    # # they might only be a few of the many files we have in the directory
    # for cls in processing_dict.keys():
    #     # get the instance of that specific class that is held inside the PointDirectory
    #     attr_as_str = cls_to_attr_name_dict.get(cls)
    #     # if the attribute does not exist for some reason, maybe the wrong class is given
    #     if not attr_as_str:
    #         raise AttributeError(
    #             f"Attribute {attr_as_str} not found in the instance of {point_directory.__class__.__name__}."
    #         )
    #     # we checked all classes subclass from HasData before, so no need to check again
    #     obj_with_data = getattr(point_directory, attr_as_str)
    #     # check if the object actually exists, because it might not be present on disk
    #     if obj_with_data:
    #         processed_data = obj_with_data.processed_data(
    #             processing_dict[cls]
    #         )
    #         all_processed_data[attr_as_str] = processed_data

    # return all_processed_data
