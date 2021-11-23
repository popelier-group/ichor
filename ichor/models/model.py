from typing import List, Optional

import numpy as np

from pathlib import Path

from ichor.common.functools import cached_property, classproperty
from ichor.common.functools.buildermethod import buildermethod
from ichor.common.str import get_digits
from ichor.files.file import File, FileContents
from ichor.models.kernels import RBF, Kernel, PeriodicKernel, RBFCyclic
from ichor.models.kernels.interpreter import KernelInterpreter
from ichor.models.kernels.periodic_kernel import PeriodicKernel
from ichor.models.mean import (ConstantMean, LinearMean, Mean, QuadraticMean,
                               ZeroMean)


class Model(File):
    """A model file that is returned back from our machine learning program FEREBUS.

    .. note::
        Another program can be used for the machine learning as long as it outputs files of the same format as the FEREBUS outputs.
    """

    # these can be accessed with __annotations__, so leave them
    system: str
    atom: str
    type: str
    nfeats: int
    ntrain: int
    mean: Mean
    k: Kernel
    x: np.ndarray
    y: np.ndarray
    nugget: float
    weights: np.ndarray

    def __init__(self, path: Path):
        File.__init__(self, path)

        self.system = FileContents
        self.atom = FileContents
        self.type = FileContents
        self.alf = FileContents
        self.nfeats = FileContents
        self.ntrain = FileContents
        self.mean = FileContents
        self.k = FileContents
        self.x = FileContents
        self.y = FileContents
        self.nugget = FileContents
        self.weights = FileContents

    @buildermethod
    def _read_file(self) -> None:
        """Read in a FEREBUS output file which contains the optimized hyperparameters, mean function, and other information that is needed to make predictions."""
        kernel_composition = ""
        kernel_list = {}

        self._nugget = 1e-10

        with open(self.path) as f:
            for line in f:
                if (
                    "nugget" in line
                ):  # noise to add to the diagonal to help with numerical stability. Typically on the scale 1e-6 to 1e-10
                    self._nugget = float(line.split()[-1])
                    continue

                if line.startswith("#"):
                    continue

                if "name" in line:  # system name e.g. WATER
                    self._system = line.split()[1]
                    continue

                if line.startswith(
                    "atom"
                ):  # atom for which a GP model was made eg. O1
                    self._atom = line.split()[1]
                    continue

                if (
                    "property" in line
                ):  # property (such as iqa or particular multipole moment) for which a GP model was made
                    self._type = line.split()[1]
                    continue

                if "ALF" in line:
                    self._alf = [int(a) for a in line.split()[1:]]
                    continue

                if "number_of_features" in line:  # number of inputs to the GP
                    self._nfeats = int(line.split()[1])
                    continue

                if (
                    "number_of_training_points" in line
                ):  # number of training points to make the GP model
                    self._ntrain = int(line.split()[1])
                    continue

                # GP mean (mu) section
                if "[mean]" in line:
                    mean_type = next(f).split()[-1]  # type
                    if mean_type == "constant":
                        self._mean = ConstantMean(float(next(f).split()[1]))
                    elif mean_type == "zero":
                        self._mean = ZeroMean()
                    elif mean_type in ["linear", "quadratic"]:
                        beta = np.array(
                            [float(b) for b in next(f).split()[1:]]
                        )
                        xmin = np.array(
                            [float(x) for x in next(f).split()[1:]]
                        )
                        ymin = float(next(f).split()[-1])
                        if mean_type == "linear":
                            self._mean = LinearMean(beta, xmin, ymin)
                        elif mean_type == "quadratic":
                            self._mean = QuadraticMean(beta, xmin, ymin)
                    continue

                if (
                    "composition" in line
                ):  # which kernels were used to make the GP model. Different kernels can be specified for different input dimensions
                    kernel_composition = line.split()[-1]
                    continue

                # GP kernel section
                if "[kernel." in line:
                    kernel_name = line.split(".")[-1].rstrip().rstrip("]")
                    line = next(f)
                    kernel_type = line.split()[-1].strip()
                    ndims = int(next(f).split()[-1])  # number of dimensions
                    line = next(f)
                    if "TODO" not in line:
                        active_dims = np.array(
                            [int(ad) - 1 for ad in line.split()[1:]]
                        )
                    else:
                        active_dims = np.arange(ndims)

                    if kernel_type == "rbf":
                        line = next(f)
                        thetas = np.array(
                            [float(hp) for hp in line.split()[1:]]
                        )
                        kernel_list[kernel_name] = RBF(
                            thetas, active_dims=active_dims
                        )
                    elif kernel_type in [
                        "rbf-cyclic",
                        "rbf-cylic",
                    ]:  # Due to typo in FEREBUS 7.0
                        line = next(f)
                        thetas = np.array(
                            [float(hp) for hp in line.split()[1:]]
                        )
                        kernel_list[kernel_name] = RBFCyclic(
                            thetas, active_dims=active_dims
                        )
                    elif kernel_type == "periodic":
                        line = next(f)
                        thetas = np.array(
                            [float(hp) for hp in line.split()[1:]]
                        )
                        kernel_list[kernel_name] = PeriodicKernel(
                            thetas,
                            np.full(thetas.shape, 2 * np.pi),
                            active_dims=active_dims,
                        )
                    continue

                # training inputs data
                if "[training_data.x]" in line:
                    line = next(f)
                    x = []
                    while line.strip() != "":
                        x += [[float(num) for num in line.split()]]
                        line = next(f)
                    self._x = np.array(x)
                    if self._x.ndim == 1:
                        self._x = self._x.reshape(-1, 1)
                    continue

                # training labels data
                if "[training_data.y]" in line:
                    line = next(f)
                    y = []
                    while line.strip() != "":
                        y += [float(line)]
                        line = next(f)
                    self._y = np.array(y)[:, np.newaxis]
                    continue

                if "[weights]" in line:
                    line = next(f)
                    weights = []
                    while line.strip() != "":
                        weights += [float(line)]
                        try:
                            line = next(f)
                        except:
                            break
                    self._weights = np.array(weights)
                    self._weights = self._weights.reshape(-1, 1)

        self._k = KernelInterpreter(
            kernel_composition, kernel_list
        ).interpret()

    @classproperty
    def filetype(self) -> str:
        """Returns the suffix associated with GP model files"""
        return ".model"

    @property
    def ialf(self) -> np.ndarray:
        return np.array(self.alf) - 1

    @property
    def atom_num(self) -> int:
        """Returns the integer that is in the atom name"""
        return get_digits(self.atom)

    @property
    def i(self) -> int:
        """Returns the integer that is one less than the one in the atom name.
        This is the index of the atom in Python objects such as lists (as indeces start at 0)."""
        return self.atom_num - 1

    def r(self, x_test: np.ndarray) -> np.ndarray:
        """ Returns the n_train by n_test covariance matrix"""
        return self.k.r(self.x, x_test)

    @cached_property
    def R(self) -> np.ndarray:
        """Returns the covariance matrix and adds a jitter to the diagonal for numerical stability. This jitter is a very
        small number on the order of 1e-6 to 1e-10."""
        return self.k.R(self.x) + (self.nugget * np.identity(self.ntrain))

    @cached_property
    def invR(self) -> np.ndarray:
        """Returns the inverse of the covariance matrix R"""
        return np.linalg.inv(self.R)

    @cached_property
    def lower_cholesky(self) -> np.ndarray:
        """Decomposes the covariance matrix into L and L^T. Returns the lower triangular matrix L."""
        return np.linalg.cholesky(self.R)

    def predict(self, x_test: np.ndarray) -> np.ndarray:
        """Returns an array containing the test point predictions."""
        return (
            self.mean.value(x_test)
            + np.dot(self.r(x_test).T, self.weights)[:, -1]
        ).flatten()

    def variance(self, x_test: np.ndarray) -> np.ndarray:
        """Return the variance for the test data points."""
        train_test_covar = self.r(x_test)
        # temporary matrix, see Rasmussen Williams page 19 algo. 2.1
        v = np.linalg.solve(self.lower_cholesky, train_test_covar)

        return np.diag(self.k.R(x_test) - np.matmul(v.T, v)).flatten()

    # TODO. model write method not implemented
    def write(self, path: Optional[Path] = None) -> None:
        pass

    def __repr__(self):
        return f"{self.__class__.__name__}(system={self.system}, atom={self.atom}, type={self.type})"
