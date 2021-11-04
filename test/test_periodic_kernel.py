import unittest
import sys

from numpy.lib.function_base import cov
sys.path.append("../ichor/")
from ichor.models.kernels.periodic_kernel import PeriodicKernel
import numpy as np

class TestPeriodicKernel(unittest.TestCase):

    def test_k_active_dims(self):
        """ Test if active dims is returning the correct number."""

        lengthscale = np.array([4.3, 2.14, 3.06, 1.73])
        thetas = 1 / (2 * lengthscale**2)
        period = 2* np.pi
        kernel = PeriodicKernel(thetas=thetas, period_length=period)
        self.assertEqual(len(kernel.params), 2)

    def test_k_periodic_one_dimension(self):
        """Test periodic covariance matrix with the same lengthscale in each dimension."""

        x1 = np.array([1.54, 1.5, 3.14]).reshape(-1,1)
        x2 = np.array([1.43, 5.23, -3.14]).reshape(-1,1)

        lengthscale = np.array([2.0])
        thetas = 1 / (2 * lengthscale**2)
        period_length = 2.0 * np.pi
        kernel = PeriodicKernel(thetas=thetas, period_length=period_length)
        cov_matrix = kernel.k(x1, x2)

        # sklearn 0.24.2 periodic kernel supports one lengthscale and seems to have a bug if the inputs are multi-dimensional
        # but sklearn gives the exact answer as our Periodic kernel implementation for one-dimensional inputs

        # lengthscale = np.array(2.0)
        # period = 2.0*np.pi
        # x1 = np.array([1.54, 1.5, 3.14]).reshape(-1,1)
        # x2 = np.array([1.43, 5.23, -3.14]).reshape(-1,1)

        # kernel = ExpSineSquared(length_scale=lengthscale, periodicity=period)
        # cov_matrix = kernel(x1, x2)

        sklearn_periodic_cov_matrix_one_dim = np.array([[0.99849017, 0.62917932, 0.7725212],
                                                        [0.99938794, 0.63257504, 0.76484549],
                                                        [0.75224844, 0.68794442, 0.99999873]])

        np.testing.assert_allclose(cov_matrix, sklearn_periodic_cov_matrix_one_dim)

    def test_k_periodic_multiple_dimensions(self):

        x1 = np.array([[1.54, -3.14, 0.98], [1.5, 3.14, 0.69], [1.343, 3.05, 0.59], [1.25, 0.98, 2.96]])
        x2 = np.array([[1.43, 5.23, 0.24], [1.23, 3.87, 1.23]])

        lengthscale = np.array([1.2, 5.39, 1.73])
        thetas = 1 / (2 * lengthscale**2)
        period_length = 2.0 * np.pi
        kernel = PeriodicKernel(thetas=thetas, period_length=period_length)
        cov_matrix = kernel.k(x1, x2)

        # custom implementation using sklearn periodic kernel, where each input-dimension covariance is calculated and multiplied
        # by other dimension covariance matrices

        # import numpy as np
        # from sklearn.gaussian_process.kernels import ExpSineSquared

        # lengthscale = np.array([1.2, 5.39, 1.73])
        # period_length = 2.0 * np.pi
        # x1 = np.array([[1.54, -3.14, 0.98], [1.5, 3.14, 0.69], [1.343, 3.05, 0.59], [1.25, 0.98, 2.96]])
        # x2 = np.array([[1.43, 5.23, 0.24], [1.23, 3.87, 1.23]])

        # x1 = x1.T
        # x2 = x2.T

        # final_cov_matrix = np.ones((4,2))

        # for idx, (one_dim_x1, one_dim_x2) in enumerate(zip(x1, x2)):

        #     kernel = ExpSineSquared(length_scale=lengthscale[idx], periodicity=period_length)
        #     cov_matrix = kernel(one_dim_x1.reshape(-1,1), one_dim_x2.reshape(-1,1))
        #     final_cov_matrix *= cov_matrix

        sklearn_periodic_cov_matrix_multi_dim = np.array([[0.86676618, 0.94915122],
                                                        [0.91716864, 0.92175724],
                                                        [0.92588932, 0.92174029],
                                                        [0.49659173, 0.63445399]])

        np.testing.assert_allclose(cov_matrix, sklearn_periodic_cov_matrix_multi_dim)

    def test_k_periodic_multiple_dimensions_covariance_matrix(self):

        x1 = np.array([[1.54, -3.14, 0.98], [1.5, 3.14, 0.69], [1.343, 3.05, 0.59], [1.25, 0.98, 2.96]])
        lengthscale = np.array([1.2, 5.39, 1.73])
        thetas = 1 / (2 * lengthscale**2)
        period_length = 2 * np.pi
        kernel = PeriodicKernel(thetas=thetas, period_length=period_length)
        cov_matrix = kernel.k(x1, x1)

        # custom implementation using sklearn periodic kernel, where each input-dimension covariance is calculated and multiplied
        # by other dimension covariance matrices

        from sklearn.gaussian_process.kernels import ExpSineSquared

        x1 = x1.T

        final_cov_matrix = np.ones((4,4))
        for idx, (one_dim_x1, one_dim_x2) in enumerate(zip(x1, x1)):
            kernel = ExpSineSquared(length_scale=lengthscale[idx], periodicity=period_length)
            final_cov_matrix *= kernel(one_dim_x1.reshape(-1,1), one_dim_x2.reshape(-1,1))
        
        sklearn_periodic_cov_matrix_multi_dim = final_cov_matrix

        np.testing.assert_allclose(cov_matrix, sklearn_periodic_cov_matrix_multi_dim)


if __name__ == "__main__":

    unittest.main()
