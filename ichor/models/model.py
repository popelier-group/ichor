from typing import List, Optional

import numpy as np

from pathlib import Path

from ichor.common.io import mkdir
from ichor.common.functools import cached_property, classproperty
from ichor.common.functools.buildermethod import buildermethod
from ichor.common.str import get_digits
from ichor.files.file import File, FileContents
from ichor.models.kernels import RBF, Kernel, PeriodicKernel, RBFCyclic, ConstantKernel
from ichor.models.kernels.interpreter import KernelInterpreter
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
    alf: List[int]
    natoms: int
    nfeats: int
    ntrain: int
    mean: Mean
    kernel: Kernel
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
        self.natoms = FileContents
        self.nfeats = FileContents
        self.ntrain = FileContents
        self.mean = FileContents
        self.kernel = FileContents
        self.x = FileContents
        self.y = FileContents
        self.nugget = FileContents
        self.weights = FileContents

    @buildermethod
    def _read_file(self) -> None:
        """Read in a FEREBUS output file which contains the optimized hyperparameters, mean function, and other information that is needed to make predictions."""
        kernel_composition = ""
        kernel_list = {}

        self.nugget = 1e-10

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
                    self.system = line.split()[1]
                    continue

                if line.startswith(
                    "atom"
                ):  # atom for which a GP model was made eg. O1
                    self.atom = line.split()[1]
                    continue

                if (
                    "property" in line
                ):  # property (such as iqa or particular multipole moment) for which a GP model was made
                    self.type = line.split()[1]
                    continue

                if "ALF" in line:
                    self.alf = [int(a) for a in line.split()[1:]]
                    continue

                if "number_of_atoms" in line:
                    self.natoms = int(line.split()[1])
                    continue

                if "number_of_features" in line:  # number of inputs to the GP
                    self.nfeats = int(line.split()[1])
                    continue

                if (
                    "number_of_training_points" in line
                ):  # number of training points to make the GP model
                    self.ntrain = int(line.split()[1])
                    continue

                # GP mean (mu) section
                if "[mean]" in line:
                    mean_type = next(f).split()[-1]  # type
                    if mean_type == "constant":
                        self.mean = ConstantMean(float(next(f).split()[1]))
                    elif mean_type == "zero":
                        self.mean = ZeroMean()
                    elif mean_type in ["linear", "quadratic"]:
                        beta = np.array(
                            [float(b) for b in next(f).split()[1:]]
                        )
                        xmin = np.array(
                            [float(x) for x in next(f).split()[1:]]
                        )
                        ymin = float(next(f).split()[-1])
                        if mean_type == "linear":
                            self.mean = LinearMean(beta, xmin, ymin)
                        elif mean_type == "quadratic":
                            self.mean = QuadraticMean(beta, xmin, ymin)
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
                        thetas = np.array(
                            [float(hp) for hp in next(f).split()[1:]]
                        )
                        kernel_list[kernel_name] = RBF(
                            kernel_name, thetas, active_dims=active_dims
                        )
                    elif kernel_type in [
                        "rbf-cyclic",
                        "rbf-cylic",
                    ]:  # Due to typo in FEREBUS 7.0
                        thetas = np.array(
                            [float(hp) for hp in next(f).split()[1:]]
                        )
                        kernel_list[kernel_name] = RBFCyclic(
                            kernel_name, thetas, active_dims=active_dims
                        )
                    elif kernel_type == "constant":
                        value = float(next(f).split()[-1])
                        kernel_list[kernel_name] = ConstantKernel(
                            kernel_name, value, active_dims=active_dims
                        )
                    elif kernel_type == "periodic":
                        thetas = np.array(
                            [float(hp) for hp in next(f).split()[1:]]
                        )
                        kernel_list[kernel_name] = PeriodicKernel(
                            kernel_name,
                            thetas,
                            np.full(thetas.shape, 2 * np.pi),
                            active_dims=active_dims,
                        )
                    continue

                # training inputs data
                if "[training_data.x]" in line:
                    line = next(f)
                    x = np.empty((self.ntrain, self.nfeats))
                    i = 0
                    while line.strip() != "":
                        x[i, :] = np.array([float(num) for num in line.split()])
                        i += 1
                        line = next(f)
                    continue

                # training labels data
                if "[training_data.y]" in line:
                    line = next(f)
                    y = np.empty((self.ntrain, 1))
                    i = 0
                    while line.strip() != "":
                        y[i, 0] = float(line)
                        i += 1
                        line = next(f)
                    continue

                if "[weights]" in line:
                    line = next(f)
                    weights = np.empty((self.ntrain, 1))
                    i = 0
                    while line.strip() != "":
                        weights[i, 0] = float(line)
                        i += 1
                        try:
                            line = next(f)
                        except:
                            break

        if kernel_composition:
            self.kernel = KernelInterpreter(kernel_composition, kernel_list).interpret()

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
        return self.kernel.r(self.x, x_test)

    @cached_property
    def R(self) -> np.ndarray:
        """Returns the covariance matrix and adds a jitter to the diagonal for numerical stability. This jitter is a very
        small number on the order of 1e-6 to 1e-10."""
        return self.kernel.R(self.x) + (self.nugget * np.identity(self.ntrain))

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

        return np.diag(self.kernel.R(x_test) - np.matmul(v.T, v)).flatten()

    def write(self, path: Optional[Path] = None) -> None:
        from ichor import __version__
        path = path or self.path

        if not path.parent.exists():
            mkdir(path.parent)
        if path.is_dir():
            path = path / f"{self.system}_{self.type}_{self.atom}{Model.filetype}"

        with open(path, 'w') as f:
            f.write("# [metadata]\n")
            f.write("# program ichor\n")
            f.write(f"# version {__version__}\n")
            f.write(f"# nugget {self.nugget}\n")
            f.write("\n")
            f.write("[system]\n")
            f.write(f"name {self.system}\n")
            f.write(f"atom {self.atom}\n")
            f.write(f"property {self.property}\n")
            f.write(f"ALF {self.alf[0]} {self.alf[1]} {self.alf[2]}\n")
            f.write("\n")
            f.write("[dimensions]\n")
            f.write(f"number_of_atoms {self.natoms}\n")
            f.write(f"number_of_features {self.nfeats}\n")
            f.write(f"number_of_training_points {self.ntrain}\n")
            f.write("\n")
            self.mean.write(f)
            f.write("\n")
            f.write("[kernels]\n")
            f.write(f"number_of_kernels {self.kernel.nkernel}\n")
            f.write(f"composition {self.kernel.name}\n")
            f.write("\n")
            self.kernel.write(f)
            f.write("\n")
            f.write("[training_data]\n")
            f.write("units.x TODO\n")
            f.write("units.y TODO\n")
            f.write("scaling.x none\n")
            f.write("scaling.y none\n")
            f.write("\n")
            f.write("[training_data.x]\n")
            for xi in self.x:
                f.write(f"{' '.join(map(str, xi))}\n")
            f.write("\n")
            f.write("[training_data.y]\n")
            f.write('\n'.join(map(str, self.y.flatten())))
            f.write("\n")
            f.write("[weights]\n")
            f.write('\n'.join(map(str, self.weights.flatten())))




    def __repr__(self):
        return f"{self.__class__.__name__}(system={self.system}, atom={self.atom}, type={self.type})"
