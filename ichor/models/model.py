import numpy as np

from ichor.common.functools import classproperty
from ichor.common.str import get_digits
from ichor.files import File
from ichor.models.kernels import RBF, Kernel, RBFCyclic
from ichor.models.kernels.interpreter import KernelInterpreter
from ichor.models.mean import ConstantMean, Mean, ZeroMean
from ichor.typing import F
from functools import wraps


def check_x_2d(func: F) -> F:
    @wraps(func)
    def wrapper(self, x, *args, **kwargs):
        if x.ndim == 1:
            x = x[np.newaxis, :]
        return func(self, x, *args, **kwargs)
    return wrapper


class Model(File):
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
        kernel_composition = ""
        kernel_list = {}

        with open(self.path) as f:
            for line in f:
                if line.startswith("#"):
                    continue

                if "name" in line:
                    self.system = line.split()[1]
                    continue
                if "property" in line:
                    self.type = line.split()[1]
                    continue
                if line.startswith("atom"):
                    self.atom = line.split()[1]
                    continue

                if "number_of_features" in line:
                    self.nfeats = int(line.split()[1])
                if "number_of_training_points" in line:
                    self.ntrain = int(line.split()[1])

                if "[mean]" in line:
                    line = next(f)
                    line = next(f)
                    self.mean = ConstantMean(float(line.split()[1]))

                if "composition" in line:
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
        # TODO: Remove loop
        for i, ri in enumerate(r):
            variance[i] = 1.0 - np.matmul(np.matmul(ri.T, invR), ri) + \
                           (np.matmul(np.matmul(ones.T, invR), ri)**2) / \
                           np.matmul(np.matmul(ones.T, invR), ones)
        return variance



    def __repr__(self):
        return (
            f"Model(system={self.system}, atom={self.atom}, type={self.type})"
        )
