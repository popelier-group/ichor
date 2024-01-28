import numpy as np


# FFLUX predicts forces in the global frame, but first predicts dQ/df in local frame
# need to predict local forces first (i.e. -dE/df), and then convert to global Cartesian forces
def fflux_gaussian_output_processing_function(c_matrix: np.ndarray) -> dict:
    """Processing function for Gaussian output file. Calculates local forces
    given a c matrix.

    :param c_matrix: rotation matrix to rotate forces with
    """

    def _processing_func(gaussian_output_instance):

        return {"rotated_forces": gaussian_output_instance.rotated_forces(c_matrix)}

    return _processing_func
