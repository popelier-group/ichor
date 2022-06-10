import numpy as np


class Distance:
    @staticmethod
    def squared_euclidean_distance(
        x1: np.ndarray, x2: np.ndarray
    ) -> np.ndarray:
        """Calculates squared distance matrix between data points, uses array broadcasting and distance trick

        .. note::
            See the following websites for how array broadcasting and the distance trick work:
            https://medium.com/@souravdey/l2-distance-matrix-vectorization-trick-26aa3247ac6c
            https://stackoverflow.com/a/37903795

        .. note::
            Does not support batches (when x1 or x2 are 3D arrays)

        Args:
            :param: `x1` np.ndarray of shape n x ndimensions:
                First matrix of n points
            :param: `x2` np.ndarray of shape m x ndimensions:
                Second marix of m points, can be identical to the first matrix `x1`

        Returns:
            :type: `np.ndarray`
                The squared distance matrix of shape (`x1.shape[0]`, `x2.shape[0]`)
        """

        result = (
            -2 * np.dot(x1, x2.T)
            + np.sum(x2**2, axis=1)
            + np.sum(x1**2, axis=1)[:, np.newaxis]
        )
        result = result.clip(
            0
        )  # small negative values may occur when using quadratic expansion, so clip to 0 if that happens

        return result

    @staticmethod
    def euclidean_distance(x1: np.ndarray, x2: np.ndarray) -> np.ndarray:
        """Calculates distance matrix between data points

        Args:
            :param: `x1` np.ndarray of shape n x ndimensions:
                First matrix of n points
            :param: `x2` np.ndarray of shape m x ndimensions:
                Second marix of m points, can be identical to the first matrix `x1`

        Returns:
            :type: `np.ndarray`
                The distance matrix of shape (n, m)
        """

        result = Distance.squared_euclidean_distance(x1, x2)
        result = np.sqrt(result)

        return result
