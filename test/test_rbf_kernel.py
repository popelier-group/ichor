import unittest
import sys
sys.path.append("../ichor/")
from ichor.models.kernels import RBF
import numpy as np

class TestRBF(unittest.TestCase):

    def test_k_active_dims(self):
        """ Test if active dims is returning the correct number."""

        lengthscale = np.array([4.3, 2.14, 3.06, 1.73])
        thetas = 1 / (2 * lengthscale**2)
        kernel = RBF(thetas=thetas)
        self.assertEqual(len(kernel.params), 4)

    def test_k_one_lengthscale(self):
        """Test RBF covariance matrix with the same lengthscale in each dimension."""

        # test with one lengthscale for all dimensions
        x1 = np.array([[1.2, 1.6, 2.24, 4.21], [0.9, 1.2, 2.03, 3.56], [1.31, 1.25, 2.01, 5.34]])
        x2 = np.array([[1.3, 1.35, 2.20, 5.12], [0.81, 1.09, 1.98, 5.49], [1.61, 1.87, 3.56, 6.01]])

        # ichor expects the number of lengthscale dimensions to be equal to the number of features
        lengthscale = np.array([2.0, 2.0, 2.0, 2.0])
        thetas = 1 / (2 * lengthscale**2)
        kernel = RBF(thetas=thetas)
        cov_matrix = kernel.k(x1, x2)

        # sklearn 0.24.2
        # import numpy as np
        # from sklearn.gaussian_process.kernels import RBF

        # lengthscale = np.array([2.0, 2.0, 2.0, 2.0])
        # x1 = np.array([[1.2, 1.6, 2.24, 4.21], [0.9, 1.2, 2.03, 3.56], [1.31, 1.25, 2.01, 5.34]])
        # x2 = np.array([[1.3, 1.35, 2.20, 5.12], [0.81, 1.09, 1.98, 5.49], [1.61, 1.87, 3.56, 6.01]])

        # kernel = RBF(length_scale=lengthscale)
        # cov_matrix = kernel(x1, x2)

        sklearn_rbf_cov_matrix_one_lengthscale = np.array([[0.89335164, 0.76737859, 0.52052102],
                                                            [0.71847455, 0.62597177, 0.31284419],
                                                            [0.98824464, 0.96331482, 0.65986171]])

        np.testing.assert_allclose(cov_matrix, sklearn_rbf_cov_matrix_one_lengthscale)

    def test_k_different_lengthscales(self):
        """ Test RBF convariance matrix with a different lengthscale in each dimension."""

        x1 = np.array([[1.2, 1.6, 2.24, 4.21], [0.9, 1.2, 2.03, 3.56], [1.31, 1.25, 2.01, 5.34]])
        x2 = np.array([[1.3, 1.35, 2.20, 5.12], [0.81, 1.09, 1.98, 5.49], [1.61, 1.87, 3.56, 6.01]])
        lengthscale = np.array([4.3, 2.14, 3.06, 1.73])
        thetas = 1 / (2 * lengthscale**2)
        kernel = RBF(thetas=thetas)
        cov_matrix = kernel.k(x1, x2)

        # sklearn 0.24.2
        # import numpy as np
        # from sklearn.gaussian_process.kernels import RBF

        # lengthscale = np.array([4.3, 2.14, 3.06, 1.73])
        # x1 = np.array([[1.2, 1.6, 2.24, 4.21], [0.9, 1.2, 2.03, 3.56], [1.31, 1.25, 2.01, 5.34]])
        # x2 = np.array([[1.3, 1.35, 2.20, 5.12], [0.81, 1.09, 1.98, 5.49], [1.61, 1.87, 3.56, 6.01]])

        # kernel = RBF(length_scale=lengthscale)
        # cov_matrix = kernel(x1, x2)
        # print(cov_matrix)

        sklearn_rbf_cov_matrix_multiple_lengthscales = np.array([[0.86456942, 0.73356806, 0.52370482],
                                                            [0.66041384, 0.53581677, 0.30408973],
                                                            [0.98895348, 0.98672651, 0.78060504]])

        np.testing.assert_allclose(cov_matrix, sklearn_rbf_cov_matrix_multiple_lengthscales)

    def test_k_different_lengthscales_with_active_dims(self):
        """ Test RBF convariance matrix with a different lengthscale in each dimension and active dims active."""

        x1 = np.array([[1.2, 1.6, 2.24, 4.21], [0.9, 1.2, 2.03, 3.56], [1.31, 1.25, 2.01, 5.34]])
        x2 = np.array([[1.3, 1.35, 2.20, 5.12], [0.81, 1.09, 1.98, 5.49], [1.61, 1.87, 3.56, 6.01]])
        lengthscale = np.array([4.3, 2.14, 3.06, 1.73])
        thetas = 1 / (2 * lengthscale**2)
        active_dims = [0,1,2]
        kernel = RBF(thetas=thetas, active_dims=active_dims)
        cov_matrix = kernel.k(x1, x2)

        # sklearn 0.24.2
        # import numpy as np
        # from sklearn.gaussian_process.kernels import RBF

        # active_dims = np.array([0,1,2])

        # lengthscale = np.array([4.3, 2.14, 3.06, 1.73])
        # x1 = np.array([[1.2, 1.6, 2.24, 4.21], [0.9, 1.2, 2.03, 3.56], [1.31, 1.25, 2.01, 5.34]])
        # x2 = np.array([[1.3, 1.35, 2.20, 5.12], [0.81, 1.09, 1.98, 5.49], [1.61, 1.87, 3.56, 6.01]])

        # kernel = RBF(length_scale=lengthscale[active_dims])
        # cov_matrix = kernel(x1[:, active_dims], x2[:,active_dims])

        sklearn_rbf_cov_matrix_with_active_dims = np.array([[0.99284612, 0.96452413, 0.89983304],
                                                            [0.99170815, 0.99832779, 0.82891097],
                                                            [0.99698238, 0.99044249, 0.84139688]])

        np.testing.assert_allclose(cov_matrix, sklearn_rbf_cov_matrix_with_active_dims)

if __name__ == "__main__":

    unittest.main()
