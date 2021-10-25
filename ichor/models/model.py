from functools import wraps
from typing import Optional

import numpy as np

from ichor.common.functools import cached_property, classproperty
from ichor.common.functools.buildermethod import buildermethod
from ichor.common.str import get_digits
from ichor.files.file import File, FileContents
from ichor.itypes import F
from ichor.models.kernels import RBF, Kernel, RBFCyclic
from ichor.models.kernels.interpreter import KernelInterpreter
from ichor.models.mean import ConstantMean, Mean, ZeroMean


class Model(File):
    """A model file that is returned back from our machine learning program FEREBUS.

    .. note::
        Another program can be used for the machine learning as long as it outputs files of the same format as the FEREBUS outputs.
    """

    # these can be accessed with __annotations__, so leave them
    _system: Optional[str]
    _atom: Optional[str]
    _type: Optional[str]
    _nfeats: Optional[int]
    _ntrain: Optional[int]
    _mean: Optional[Mean]
    _k: Optional[Kernel]
    _x: Optional[np.ndarray]
    _y: Optional[np.ndarray]

    nugget: Optional[float] = None

    def __init__(self, path):
        File.__init__(self, path)

        self._system: Optional[str] = FileContents
        self._atom: Optional[str] = FileContents
        self._type: Optional[str] = FileContents
        self._nfeats: Optional[int] = FileContents
        self._ntrain: Optional[int] = FileContents
        self._mean: Optional[Mean] = FileContents
        self._k: Optional[Kernel] = FileContents
        self._x: Optional[np.ndarray] = FileContents
        self._y: Optional[np.ndarray] = FileContents
        self._nugget = 1e-10  # todo: read this from ferebus file as well
        self._weights = None  # todo: read this from ferebus file as well

    @buildermethod
    def _read_file(self) -> None:
        """Read in a FEREBUS output file which contains the optimized hyperparameters, mean function, and other information that is needed to make predictions."""
        kernel_composition = ""
        kernel_list = {}

        with open(self.path) as f:
            for line in f:
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

                if "nugget" in line:  # noise to add to the diagonal to help with numerical stability. Typically on the scale 1e-6 to 1e-10
                    self._nugget = float(line.split()[-1])
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
                    _ = next(f)
                    line = next(f)
                    self._mean = ConstantMean(float(line.split()[1]))
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

                    if kernel_type == "rbf":
                        _ = next(f)
                        _ = next(f)
                        line = next(f)
                        thetas = np.array(
                            [float(hp) for hp in line.split()[1:]]
                        ).reshape(1,-1)
                        kernel_list[kernel_name] = RBF(thetas)
                    elif kernel_type in [
                        "rbf-cyclic",
                        "rbf-cylic",
                    ]:  # Due to typo in FEREBUS 7.0
                        line = next(f)
                        line = next(f)
                        line = next(f)
                        thetas = np.array(
                            [float(hp) for hp in line.split()[1:]]
                        )
                        kernel_list[kernel_name] = RBFCyclic(thetas)
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
                        self._x = self._x.reshape(-1,1)
                    continue

                # training labels data
                if "[training_data.y]" in line:
                    line = next(f)
                    y = []
                    while line.strip() != "":
                        y += [float(line)]
                        line = next(f)
                    self._y = np.array(y)
                    self._y = self._y.reshape(-1,1)
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

        self.k = KernelInterpreter(kernel_composition, kernel_list).interpret()

    @classproperty
    def filetype(self) -> str:
        """ Returns the suffix associated with GP model files"""
        return ".model"

    @cached_property
    def system(self) -> str:
        """ Returns the system name"""
        return self._system

    @cached_property
    def atom(self) -> str:
        """ Returns the atom name for which a GP model was made"""
        return self._atom

    @cached_property
    def type(self) -> str:
        """ Returns the property (iqa, q00, etc) for which a GP model was made"""
        return self._type

    @cached_property
    def nugget(self) -> float:
        """ Returns the nugget/jitter that is added to the diagonal of the train-train covariance matrix to ensure numerical stability
        of the cholesky decomposition. This is a small number on the order of 1e-6 to 1e-10."""
        return self._nugget

    @cached_property
    def nfeats(self) -> int:
        """ Returns the number of features"""
        return self._nfeats

    @cached_property
    def ntrain(self) -> int:
        """ Returns the number of training points"""
        return self._ntrain

    @cached_property
    def mean(self) -> int:
        """ Returns the GP mean value (mu)"""
        return self._mean

    @cached_property
    def k(self) -> str:
        """ Returns the name of the covariance function used to calculate the covariance matrix"""
        return self._k

    @cached_property
    def x(self) -> np.ndarray:
        """ Returns the. training inputs numpy array Shape `n_points x n_features`"""
        return self._x

    @cached_property
    def y(self) -> np.ndarray:
        """ Returns the training outputs numpy array. Shape `n_points`"""
        return self._y

    @cached_property
    def atom_num(self) -> int:
        """ Returns the integer that is in the atom name"""
        return get_digits(self.atom)

    @cached_property
    def i(self) -> int:
        """ Returns the integer that is one less than the one in the atom name.
        This is the index of the atom in Python objects such as lists (as indeces start at 0)."""
        return self.atom_num - 1

    def r(self, x: np.ndarray) -> np.ndarray:
        return self.k.r(self.x, x)

    @cached_property
    def weights(self) -> np.ndarray:
        """ Returns an array containing the weights which can be stored prior to making predictions."""
        return np.linalg.solve(self.lower_cholesky.T, np.linalg.solve(self.lower_cholesky, self.y-self.mean.value(self.x)))

    @cached_property
    def R(self) -> np.ndarray:
        """ Returns the covariance matrix and adds a jitter to the diagonal for numerical stability. This jitter is a very 
            small number on the order of 1e-6 to 1e-10."""
        return self.k.R(self.x) + (self.nugget * np.eye(self.ntrain))

    @cached_property
    def lower_cholesky(self) -> np.ndarray:
        """ Decomposes the covariance matrix into L and L^T. Returns the lower triangular matrix L."""
        return np.linalg.cholesky(self.R)

    def predict(self, x_test: np.ndarray) -> np.ndarray:
        """ Returns an array containing the test point predictions."""
        return (self.mean.value(self.x) + np.dot(self.k.r(self.x, x_test).T, self.weights)).flatten()

    def variance(self, x_test: np.ndarray) -> np.ndarray:
        """ Return the variance for the test data points."""
        train_test_covar = self.k.r(self.x, x_test)
        # temporary matrix, see Rasmussen Williams page 19 algo. 2.1
        v = np.linalg.solve(self.lower_cholesky, train_test_covar)

        return np.diag(self.R - np.matmul(v, v.T)).flatten()

    # TODO. model write method not implemented
    def write(self) -> None:
        pass

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(system={self.system}, atom={self.atom}, type={self.type})"
        )
