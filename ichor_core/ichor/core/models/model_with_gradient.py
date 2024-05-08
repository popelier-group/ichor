from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from ichor.core.atoms import ALF
from ichor.core.common.str import get_digits
from ichor.core.files.file import FileContents, ReadFile
from ichor.core.models.kernels import Kernel, MixedKernelWithDerivatives


class ModelWithGradients(ReadFile):

    _filetype = ".model"

    def __init__(
        self,
        path: Path,
    ):
        super(ReadFile, self).__init__(path)

        self.program = FileContents
        self.system_name: str = FileContents
        self.atom_name: str = FileContents
        self.prop: str = FileContents
        self.alf: ALF = FileContents
        self.natoms: int = FileContents
        self.nfeats: int = FileContents
        self.ntrain: int = FileContents
        self.mean: float = FileContents
        self.kernel: Kernel = FileContents
        self.x: np.ndarray = FileContents
        self.y: np.ndarray = FileContents
        self.input_units: List[str] = FileContents
        self.output_unit: str = FileContents
        self.task_noises: np.ndarray = FileContents
        self.program: str = FileContents
        self.program_version: str = FileContents
        self.notes: Dict[str, str] = FileContents
        self.weights = FileContents

        self.rbf_thetas = FileContents
        self.periodic_thetas = FileContents
        self.rbf_active_dims = FileContents
        self.periodic_active_dims = FileContents

    def _read_file(self, up_to: Optional[str] = None):
        """Read in a FEREBUS output file which contains the optimized
        hyperparameters, mean function, and other information that is needed to make predictions."""

        with open(self.path, "r") as f:

            for line in f:

                if "program" in line:
                    self.program = self.program or line.split()[-1]
                    continue

                if "task noises" in line:
                    # noise to add to the diagonal to help with numerical stability.
                    # Typically on the scale 1e-6 to 1e-10
                    self.task_noises = np.array(list(map(float, line.split()[3:])))
                    continue

                if "name" in line:  # system name e.g. WATER
                    self.system_name = self.system_name or line.split()[1]
                    continue

                if line.startswith("atom"):  # atom for which a GP model was made eg. O1
                    self.atom_name = self.atom_name or line.split()[1].capitalize()
                    continue

                if (
                    "property" in line
                ):  # property (such as iqa or particular multipole moment) for which a GP model was made
                    self.prop = self.prop or line.split()[1]
                    continue

                if "ALF" in line:
                    tmp_line_split = line.split()[1:]
                    if tmp_line_split[-1] == "None":
                        self.alf = self.alf or ALF(
                            *[int(a) - 1 for a in line.split()[1:-1]], None
                        )
                    else:
                        self.alf = self.alf or ALF(
                            *[int(a) - 1 for a in line.split()[1:]]
                        )
                    continue

                if "number_of_atoms" in line:
                    self.natoms = self.natoms or int(line.split()[1])
                    continue

                if "number_of_features" in line:  # number of inputs to the GP
                    self.nfeats = self.nfeats or int(line.split()[1])
                    continue

                if (
                    "number_of_training_points" in line
                ):  # number of training points to make the GP model
                    self.ntrain = self.ntrain or int(line.split()[1])
                    continue

                # GP mean (mu) section
                if "[mean]" in line:
                    mean_type = next(f).split()[-1]  # type
                    if mean_type == "constant":
                        # the first ntrain entries of self.mean are for energies, so get
                        # the constant mean there
                        # the rest of the values in the mean are going to be 0 because the derivative
                        # of a constant mean is 0
                        constant_mean_energies = np.array([float(next(f).split()[1])])
                        constant_mean_forces = np.zeros(self.nfeats)
                        self.mean = np.concatenate(
                            (constant_mean_energies, constant_mean_forces)
                        )[..., np.newaxis]
                    continue

                # GP kernel section
                if "[kernel." in line:
                    line = next(f)
                    kernel_type = line.split()[-1].strip()
                    line = next(f)  # skip the number of dimensions
                    line = next(f)
                    active_dims = np.array([int(ad) - 1 for ad in line.split()[1:]])
                    if kernel_type == "rbf":
                        rbf_thetas = np.array([float(hp) for hp in next(f).split()[1:]])
                        self.rbf_thetas = rbf_thetas
                        self.rbf_active_dims = active_dims
                    elif kernel_type == "periodic":
                        periodic_thetas = np.array(
                            [float(hp) for hp in next(f).split()[1:]]
                        )
                        self.periodic_thetas = periodic_thetas
                        self.periodic_active_dims = active_dims
                    continue

                if "units.x" in line:
                    self.input_units = self.input_units or line.split()[1:]
                    continue

                if "units.y" in line:
                    self.output_unit = self.output_unit or line.split()[-1]
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
                    self.x = self.x or x
                    continue

                # training labels data
                if "[training_data.y]" in line:
                    line = next(f)
                    y = np.empty((self.ntrain, 1 + self.nfeats))
                    i = 0
                    j = 0
                    while line.strip() != "":
                        # get the wfn energy and all gradient info
                        for l in line.split():
                            y[i, j] = float(l)
                            j += 1
                        # go to next row, reset column
                        i += 1
                        j = 0
                        line = next(f)
                    self.y = self.y or y
                    continue

                if "[weights]" in line:
                    line = next(f)
                    weights = np.empty((self.ntrain * (self.nfeats + 1), 1))
                    i = 0
                    while line.strip() != "":
                        weights[i, 0] = float(line)
                        i += 1
                        try:
                            line = next(f)
                        except StopIteration:
                            break

                    self.weights = weights
                    continue

        self.kernel = MixedKernelWithDerivatives(
            "k",
            self.rbf_thetas,
            self.periodic_thetas,
            self.rbf_active_dims,
            self.periodic_active_dims,
        )

    @property
    def ialf(self) -> np.ndarray:
        """Returns the atomic local frame, indices start at 0 (as in Python).

        :return: The 0-indexed np.ndarray corresponding to the alf of the atom.
        """
        return np.array(self.alf)

    @property
    def type(self) -> str:
        """alias for prop"""
        return self.prop

    @property
    def atom(self) -> str:
        """alias for atom_name"""
        return self.atom_name

    @property
    def atom_num(self) -> int:
        """Returns the integer that is in the atom name"""
        return get_digits(self.atom_name)

    @property
    def i(self) -> int:
        """Returns the integer that is one less than the one in the atom name.
        This is the index of the atom in Python objects such as lists (as indeces start at 0)."""
        return self.atom_num - 1

    def r(self, x_test: np.ndarray) -> np.ndarray:
        """Returns the n_train by n_test covariance matrix"""
        return self.kernel.r(self.x, x_test)

    @property
    def R(self) -> np.ndarray:
        """Returns the covariance matrix and adds a jitter
        to the diagonal for numerical stability. This jitter is a very
        small number on the order of 1e-6 to 1e-10."""
        return self.kernel.R(self.x)

    @property
    def invR(self) -> np.ndarray:
        """Returns the inverse of the covariance matrix R"""
        return np.linalg.inv(self.R)

    @property
    def lower_cholesky(self) -> np.ndarray:
        """Decomposes the covariance matrix into L and L^T. Returns the lower triangular matrix L."""
        return np.linalg.cholesky(self.R)

    @property
    def logdet(self):
        sign, logdet = np.linalg.slogdet(self.R)
        return sign * logdet

    def predict(self, x_test: np.ndarray) -> np.ndarray:
        """Returns an array containing the test point predictions."""

        return self.mean + self.r(x_test).T @ self.weights

    def variance(self, x_test: np.ndarray) -> np.ndarray:
        """Return the variance for the test data points."""
        train_test_covar = self.r(x_test)
        # temporary matrix, see Rasmussen Williams page 19 algo. 2.1
        v = np.linalg.solve(self.lower_cholesky, train_test_covar)

        # TODO: need to multiply by tau^2 in order to get "true" variance which can be used for error estimations.
        # here it can only be used to compare points to figure out which point has the largest variance.
        return 1.0 - np.diag(np.matmul(v.T, v)).flatten()

    def __repr__(self):
        return f"{self.__class__.__name__}(system={self.system_name}, atom={self.atom_name}, type={self.prop})"
