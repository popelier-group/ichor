from functools import wraps

import numpy as np

from ichor.common.functools import classproperty
from ichor.common.str import get_digits
from ichor.files import File
from ichor.models.kernels import RBF, Kernel, RBFCyclic
from ichor.models.kernels.interpreter import KernelInterpreter
from ichor.models.mean import ConstantMean, Mean, ZeroMean
from ichor.typing import F


def check_x_2d(func: F) -> F:
    @wraps(func)
    def wrapper(self, x, *args, **kwargs):
        if x.ndim == 1:
            x = x[np.newaxis, :]
        return func(self, x, *args, **kwargs)

    return wrapper


class Model(File):
    """ A model file that is returned back from our machine learning program FEREBUS.
    
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
    weights: np.ndarray

    def __init__(self, path):
        File.__init__(self, path)

    def _read_file(self) -> None:
        """ Read in a FEREBUS output file which contains the optimized hyperparameters, mean function, and other information that is needed to make predictions."""
        kernel_composition = ""
        kernel_list = {}

        # matt_todo: These can probably be if elif statements instead of all if
        with open(self.path) as f:
            for line in f:
                if line.startswith("#"):
                    continue

                if "name" in line:  # system name e.g. WATER
                    self.system = line.split()[1]
                    continue
                if "property" in line:  # property (such as IQA or particular multipole moment) for which a GP model was made
                    self.type = line.split()[1]
                    continue
                if line.startswith("atom"):  # atom for which a GP model was made
                    self.atom = line.split()[1]
                    continue

                if "number_of_features" in line:  # number of inputs to the GP (3N-6 features)
                    self.nfeats = int(line.split()[1])
                if "number_of_training_points" in line:  # number of training points to make the GP model
                    self.ntrain = int(line.split()[1])

                if "[mean]" in line:  # A section for specifying the mean of the GP
                    line = next(f)
                    line = next(f)
                    self.mean = ConstantMean(float(line.split()[1]))

                if "composition" in line:  # which kernels were used to make the GP model. Different kernels can be specified for different input dimensions
                    kernel_composition = line.split()[-1]

                if "[kernel." in line:
                    kernel_name = line.split(".")[-1].rstrip().rstrip("]")
                    line = next(f)
                    kernel_type = line.split()[-1].strip()

                    if kernel_type == "rbf":
                        line = next(f)
                        line = next(f)
                        line = next(f)
                        lengthscale = np.array(
                            [float(hp) for hp in line.split()[1:]]
                        )
                        # matt_todo: Rename theta to lengthscale in ferebus because it is more widely used / easier to think about
                        # TODO: Change theta from FEREBUS to lengthscale to match label
                        lengthscale = np.sqrt(1 / (2.0 * lengthscale))
                        kernel_list[kernel_name] = RBF(lengthscale)
                    elif kernel_type in [
                        "rbf-cyclic",
                        "rbf-cylic",
                    ]:  # Due to typo in FEREBUS 7.0
                        line = next(f)
                        line = next(f)
                        line = next(f)
                        lengthscale = np.array(
                            [float(hp) for hp in line.split()[1:]]
                        )
                        kernel_list[kernel_name] = RBFCyclic(lengthscale)

                if "[training_data.x]" in line:
                    line = next(f)
                    x = []
                    while line.strip() != "":
                        x += [[float(num) for num in line.split()]]
                        line = next(f)
                    self.x = np.array(x)

                if "[training_data.y]" in line:
                    line = next(f)
                    y = []
                    while line.strip() != "":
                        y += [float(line)]
                        line = next(f)
                    self.y = np.array(y)

                if "[weights]" in line:
                    line = next(f)
                    weights = []
                    while line.strip() != "":
                        weights += [float(line)]
                        try:
                            line = next(f)
                        except:
                            break
                    self.weights = np.array(weights)

        self.k = KernelInterpreter(kernel_composition, kernel_list).interpret()

    @classproperty
    def filetype(self) -> str:
        return ".model"

    def write(self) -> None:
        pass

    @property
    def atom_num(self) -> int:
        return get_digits(self.atom)

    @property
    def i(self) -> int:
        return self.atom_num - 1

    @check_x_2d
    def r(self, x: np.ndarray) -> np.ndarray:
        return self.k.r(self.x, x)

    @property
    def R(self) -> np.ndarray:
        return self.k.R(self.x)

    @property
    def invR(self) -> np.ndarray:
        return np.linalg.inv(self.R)

    @check_x_2d
    def predict(self, x: np.ndarray) -> np.ndarray:
        r = self.k.r(self.x, x)
        return self.mean.value(x) + np.matmul(r, self.weights)

    @check_x_2d
    def variance(self, x: np.ndarray) -> np.ndarray:
        r = self.k.r(self.x, x)
        invR = self.invR
        ones = np.ones((self.ntrain, 1))
        variance = np.empty(len(x))
        res3 = np.matmul(np.matmul(ones.T, invR), ones)

        print(r)
        quit()
        # TODO: Remove loop
        for i, ri in enumerate(r):
            res1 = np.matmul(np.matmul(ri.T, invR), ri)
            res2 = (1.0 - np.matmul(np.matmul(ones.T, invR), ri)) ** 2
            variance[i] = 1.0 - res1 + res2 / res3
        return variance

    def __repr__(self):
        return (
            f"Model(system={self.system}, atom={self.atom}, type={self.type})"
        )
