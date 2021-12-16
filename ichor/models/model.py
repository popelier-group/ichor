from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from ichor.common.functools import cached_property, classproperty
from ichor.common.functools.buildermethod import buildermethod
from ichor.common.io import mkdir
from ichor.common.str import get_digits
from ichor.common.types import Version
from ichor.files.file import File, FileContents
from ichor.globals import GLOBALS
from ichor.models.kernels import (RBF, ConstantKernel, Kernel, PeriodicKernel,
                                  RBFCyclic)
from ichor.models.kernels.interpreter import KernelInterpreter
from ichor.models.mean import (ConstantMean, LinearMean, Mean, QuadraticMean,
                               ZeroMean)


def _get_default_input_units(nfeats: int) -> List[str]:
    units = []
    for i in range(min(nfeats, 3)):
        units += [["bohr", "bohr", "radians"][i]]
    for i in range(3, nfeats):
        units += [["bohr", "radians", "radians"][i % 3]]
    return units


def _get_default_output_unit(property: str) -> str:
    if property == "iqa":
        return "Ha"
    elif property == "q00":
        return "e"
    else:
        return "unknown"


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
    input_units: List[str]
    output_unit: str
    likelihood: float
    nugget: float
    weights: np.ndarray
    program: str
    program_version: Version
    notes: Dict[str, str]

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
        self.input_units = FileContents
        self.output_unit = FileContents
        self.likelihood = FileContents
        self.nugget = FileContents
        self.weights = FileContents
        self.program = FileContents
        self.program_version = FileContents
        self.notes = FileContents

    @buildermethod
    def _read_file(self, up_to: Optional[str] = None) -> None:
        """Read in a FEREBUS output file which contains the optimized hyperparameters, mean function, and other information that is needed to make predictions."""
        kernel_composition = ""
        kernel_list = {}

        self.notes = {}
        self.nugget = 1e-10

        stopiter = False

        with open(self.path) as f:
            for line in f:
                if stopiter:
                    break

                if up_to is not None and up_to in line:
                    stopiter = True

                if "<TODO>" in line:
                    continue

                if "program" in line:
                    self.program = line.split()[-1]
                    continue

                if "version" in line:
                    self.program_version = Version(line.split()[-1])
                    continue

                if (
                    "nugget" in line
                ):  # noise to add to the diagonal to help with numerical stability. Typically on the scale 1e-6 to 1e-10
                    self.nugget = float(line.split()[-1])
                    continue

                if "likelihood" in line:
                    self.likelihood = float(line.split()[-1])
                    continue

                if "#" in line and "=" in line:
                    line = line.lstrip("#")
                    key, val = line.split("=")
                    self.notes[key.strip()] = val.strip()
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

                if "units.x" in line:
                    self.input_units = line.split()[1:]

                if "units.y" in line:
                    self.output_unit = line.split()[-1]

                # training inputs data
                if "[training_data.x]" in line:
                    line = next(f)
                    self.x = np.empty((self.ntrain, self.nfeats))
                    i = 0
                    while line.strip() != "":
                        self.x[i, :] = np.array(
                            [float(num) for num in line.split()]
                        )
                        i += 1
                        line = next(f)
                    continue

                # training labels data
                if "[training_data.y]" in line:
                    line = next(f)
                    self.y = np.empty((self.ntrain, 1))
                    i = 0
                    while line.strip() != "":
                        self.y[i, 0] = float(line)
                        i += 1
                        line = next(f)
                    continue

                if "[weights]" in line:
                    line = next(f)
                    self.weights = np.empty((self.ntrain, 1))
                    i = 0
                    while line.strip() != "":
                        self.weights[i, 0] = float(line)
                        i += 1
                        try:
                            line = next(f)
                        except:
                            break

        if kernel_composition:
            self.kernel = KernelInterpreter(
                kernel_composition, kernel_list
            ).interpret()

    @property
    def atom_name(self) -> str:
        return self.atom

    @atom_name.setter
    def atom_name(self, value: str):
        self.atom = value

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
        """Returns the n_train by n_test covariance matrix"""
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

    @cached_property
    def _y_minus_mean(self):
        return self.y - self.mean.value(self.x).reshape((-1, 1))

    @cached_property
    def logdet(self):
        sign, logdet = np.linalg.slogdet(self.R)
        return sign * logdet

    def compute_weights(self) -> np.ndarray:
        """Computes the training weights from the data given"""
        return np.linalg.solve(self.lower_cholesky, self._y_minus_mean)

    def compute_likelihood(self) -> float:
        """Computes the marginal likelihood from the data given"""
        return (
            0.5 * np.dot(self._y_minus_mean.T, self.compute_weights()).item()
            - 0.5 * self.logdet
            - 0.5 * self.ntrain * np.log(2 * np.pi)
        )

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

    def validate(self):
        from ichor import __version__

        self.program = (
            self.program if self.program is not FileContents else "ichor"
        )
        self.program_version = (
            self.program_version
            if self.program_version is not FileContents
            else __version__
        )
        self.nugget = self.nugget if self.nugget is not FileContents else 1e-10

        self.system = (
            self.system
            if self.system is not FileContents
            else GLOBALS.SYSTEM_NAME
        )
        self.atom = self.atom if self.atom is not FileContents else "X1"
        self.type = self.type if self.type is not FileContents else "p1"
        self.alf = self.alf if self.alf is not FileContents else [1, 1, 1]

        if self.x is not FileContents:
            if self.x.ndim == 1:
                self.x = self.x.reshape(1, -1)
            elif self.x.ndim != 2:
                raise ValueError(
                    f"Training Input (x) must be 2D, {self.x.ndim}D array encountered"
                )
            if self.nfeats is FileContents:
                self.nfeats = self.x.shape[1]
            if self.ntrain is FileContents:
                self.ntrain = self.x.shape[0]

        if self.nfeats is FileContents and self.natoms is not FileContents:
            self.nfeats = 3 * self.natoms - 6

        if self.natoms is FileContents and self.nfeats is not FileContents:
            self.natoms = (self.nfeats + 6) // 3

        if self.natoms is FileContents:
            self.natoms = 1

        if self.nfeats is FileContents:
            self.nfeats = 0

        if self.ntrain is FileContents:
            self.ntrain = 0

        if self.x is FileContents:
            self.x = np.zeros((self.ntrain, self.nfeats))

        if self.y is FileContents:
            self.y = np.zeros((self.ntrain, 1))

        if self.input_units is FileContents:
            self.input_units = _get_default_input_units(self.nfeats)

        if self.output_unit is FileContents:
            self.output_unit = _get_default_output_unit(self.type)

        if self.kernel is FileContents:
            self.kernel = RBFCyclic("k1", np.ones(self.nfeats))

        if self.mean is FileContents:
            if self.ntrain == 0:
                self.mean = ConstantMean(0.0)
            else:
                self.mean = ConstantMean(np.mean(self.y.flatten()))

        if self.likelihood is FileContents:
            self.likelihood = self.compute_likelihood()

        if self.weights is FileContents:
            self.weights = self.compute_weights()

    def write(self, path: Optional[Path] = None) -> None:
        path = path or self.path

        if not path.parent.exists():
            mkdir(path.parent)
        if path.is_dir():
            path = (
                path / f"{self.system}_{self.type}_{self.atom}{Model.filetype}"
            )

        with self.block():
            self.validate()

        with open(path, "w") as f:
            f.write("# [metadata]\n")
            f.write(f"# program {self.program}\n")
            f.write(f"# version {self.program_version}\n")
            f.write(f"# nugget {self.nugget}\n")
            f.write(f"# likelihood {self.likelihood}\n")
            for key, val in self.notes.items():
                f.write(f"# {key} = {val}\n")
            f.write("\n")
            f.write("[system]\n")
            f.write(f"name {self.system}\n")
            f.write(f"atom {self.atom}\n")
            f.write(f"property {self.type}\n")
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
            f.write(f"units.x {' '.join(self.input_units)}\n")
            f.write(f"units.y {self.output_unit}\n")
            f.write("scaling.x none\n")
            f.write("scaling.y none\n")
            f.write("\n")
            f.write("[training_data.x]\n")
            for xi in self.x:
                f.write(f"{' '.join(map(str, xi))}\n")
            f.write("\n")
            f.write("[training_data.y]\n")
            f.write("\n".join(map(str, self.y.flatten())))
            f.write("\n\n")
            f.write("[weights]\n")
            f.write("\n".join(map(str, self.weights.flatten())))
            f.write("\n")

    def __repr__(self):
        return f"{self.__class__.__name__}(system={self.system}, atom={self.atom}, type={self.type})"
