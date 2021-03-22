import numpy as np
from ichor.models.kernels.kernel import Kernel
from ichor.models.kernels.distance import Distance


class RBFCyclicKernel(Kernel):
    """Implemtation of Radial Basis Function (RBF) kernel with cyclic feature correction for phi angle feature
    
    .. note::
        Cyclic correction is applied only for our phi angles (phi is the azimuthal angle measured in the xy plane).

        If we have unstandardized(original) features, we have to apply this correction only when the distance between two phi angles is greater than pi

        .. math::

            \phi_1 - \phi_2 = \left \{
            \begin{aligned}
            &\phi_1 - \phi_2, && \text{if}\ \phi_1 - \phi_2 \leq \pi \\
            & 2\pi - (\phi_1 - \phi_2), && \text{if}\ (\phi_1 - \phi_2) \geq \pi
            \end{aligned} \right.
        
        If we have standardized features (where we have subtracted the feature mean and divided by the feature standard deviation),
        we have to apply a correction only when the distance is greater than pi/sigma where sigma is the standard deviation of
        the particular feature in the training data.

        .. math::

            \hat \phi_1 - \hat \phi_2 = \left \{
            \begin{aligned}
            &\hat \phi_1 - \hat \phi_2, && \text{if}\ \hat \phi_1 - \hat \phi_2 \leq \frac{\pi}{\sigma} \\
            & \frac{2\pi}{\sigma} - (\hat \phi_1 - \hat \phi_2), && \text{if}\ (\hat \phi_1 - \hat \phi_2) \geq \frac{\pi}{\sigma}
            \end{aligned} \right.    
    """

    def __init__(self, lengthscale: np.ndarray):
        
        self._lengthscale = lengthscale

    @property
    def params(self):
        return self._lengthscale

    def k(self, x1: np.ndarray, x2: np.ndarray) -> np.ndarray:
        """ Calcualtes cyclic RBF covariance matrix from two sets of points

        Args:
            :param: `x1` np.ndarray of shape n x ndimensions:
                First matrix of n points
            :param: `x2` np.ndarray of shape m x ndimensions:
                Second marix of m points, can be identical to the first matrix `x1`

        Returns:
            :type: `np.ndarray`
                The cyclic RBF covariance matrix matrix of shape (n, m)
        """

        # TODO: lengthscales vs thetas. Using lengthscales simplifies the code here because you can divide inputs prior to computing distance matrix
        # TODO: using thetas which are 0.5*l^-2 then means you cannot just multiply by -theta here because they already include l^-2 instead of l^-1 
        x1 = x1 * - self._lengthscale
        x2 = x2 * - self._lengthscale

        dist = Distance.squared_euclidean_distance(x1, x2)

        return np.exp(dist)

    def r(self, x_test: np.ndarray, x_train: np.ndarray) -> np.ndarray:
        """ helper method to return x_test, x_train cyclic RBF covariance matrix K(X*, X)"""

        return self.k(x_test, x_train)

    def R(self, x_train: np.ndarray) -> np.ndarray:
        """ helper method to return symmetric square matrix x_train, x_train cyclic RBF covariance matrix K(X, X)"""

        return self.k(x_train, x_train)
