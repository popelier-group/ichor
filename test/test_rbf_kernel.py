import unittest
import sys
sys.path.append("../ichor/")
from ichor.models.kernels import RBF

class RBFTest(unittest.TestCase):

    def test_k(self):
        """ Test if covariance matrix matches the given matrix"""

        kernel = RBF(thetas=0.5)
        cov_matrix = kernel.k(np.arrange)


    def test_k_higher_dims(self):

        pass

    def test_k_active_dims(self):

        pass

if __name__ == "__main__":

    unittest.main()
