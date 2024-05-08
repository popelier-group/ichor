from typing import Dict

import numpy as np
from ichor.core.files import Int, IntDirectory


def fflux_int_processing_function(c_matrix: np.ndarray):
    def _processing_data_func(int_file_instance: Int):

        return {
            **{"iqa": int_file_instance.iqa},
            **{"integration_error": int_file_instance.integration_error},
            **int_file_instance.local_spherical_multipoles(c_matrix),
        }

    return _processing_data_func


def fflux_ints_directory_processing_function(c_matrix_dict: Dict[str, np.ndarray]):
    """
    Processes all data relating to an IntDirectory and returns a dictionary of key: atom_name,
    value: processed data for that atom from multiple int files.

    At the moment, only A' data (encomp=3) can be processed.

    :param processing_func: callable to be passed to Int file instance
        which does the processing
    """

    def _processing_data_func(int_directory_instance: IntDirectory):

        dat = {}

        for atm_name, c_mat in c_matrix_dict.items():
            atm_name = atm_name.capitalize()
            int_file = int_directory_instance[atm_name]
            processed_dat = int_file.processed_data(
                fflux_int_processing_function(c_mat)
            )
            dat[atm_name] = processed_dat

        return dat

    return _processing_data_func
