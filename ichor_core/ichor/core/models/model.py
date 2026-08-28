from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from ichor.core.atoms import ALF
from ichor.core.common.io import mkdir
from ichor.core.common.str import get_digits
from ichor.core.common.types import Version
from ichor.core.files.file import (
    FileContents,
    FileReadError,
    ReadFile,
    WriteFile,
)
from ichor.core.models.kernels import (
    ConstantKernel,
    Kernel,
    PeriodicKernel,
    RBF,
    RBFCyclic,
)
from ichor.core.models.kernels.interpreter import KernelInterpreter
from ichor.core.models.mean import (
    ConstantMean,
    LinearMean,
    Mean,
    QuadraticMean,
    ZeroMean,
)


def _get_default_input_units(nfeats: int) -> List[str]:
    units = [["bohr", "bohr", "radians"][i] for i in range(min(nfeats, 3))]
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


class Model(ReadFile, WriteFile):
    """A model file that is returned back from our machine learning program FEREBUS.

    .. note::
        Another program can be used for the machine learning as
        long as it outputs files of the same format as the FEREBUS outputs.
    """

    _filetype = ".model"

    def __init__(
        self,
        path: Path,
        system_name: str = FileContents,
        atom_name: str = FileContents,
        prop: str = FileContents,
        alf: ALF = FileContents,
        natoms: int = FileContents,
        ntrain: int = FileContents,
        nfeats: int = FileContents,
        mean: Mean = FileContents,
        kernel: Kernel = FileContents,
        x: np.ndarray = FileContents,
        y: np.ndarray = FileContents,
        input_units: List[str] = FileContents,
        output_unit: str = FileContents,
        likelihood: float = FileContents,
        jitter: float = FileContents,
        weights: np.ndarray = FileContents,
        program: str = FileContents,
        program_version: Version = FileContents,
        notes: Dict[str, str] = FileContents,
    ):
        super(ReadFile, self).__init__(path)

        self.program = program
        self.system_name = system_name
        self.atom_name = atom_name
        self.prop = prop
        self.alf = alf
        self.natoms = natoms
        self.nfeats = nfeats
        self.ntrain = ntrain
        self.mean = mean
        self.kernel = kernel
        self.x = x
        self.y = y
        self.input_units = input_units
        self.output_unit = output_unit
        self.likelihood = likelihood
        self.jitter = jitter
        self.weights = weights
        self.program_version = program_version
        self.notes = notes

    def _read_data_block(self, f, block_name: str, ncols: int) -> np.ndarray:
        """Reads one of the fixed-size data blocks of a model file (the training
        inputs, the training labels or the weights) into an array.

        Every one of those blocks holds one row per training point, so the array is
        allocated from the ``number_of_training_points`` of the header and the block
        is required to fill it exactly. A block which does not is an error rather than
        something to work around: the rows are read into uninitialised memory, so a
        short block would otherwise leave whatever happened to be on the heap in the
        tail of the array and go on to be used as if it were data. That is silent -
        the model still predicts, it just predicts from values that were never in the
        file - and it is the sort of thing a Fortran write overflow produces for one
        atom of a system while leaving every other file intact.

        :param f: the open model file, positioned on the line naming the block.
        :param block_name: the name of the block, used in the error messages.
        :param ncols: how many values each row of the block holds.
        :raises FileReadError: if the block is not exactly ``ntrain`` rows of
            ``ncols`` numbers.
        :return: the block, of shape (ntrain, ncols).
        """

        rows = []
        # the block runs to the next blank line, or to the end of the file if it is
        # the last one (the weights usually are)
        for line in f:
            if not line.strip():
                break
            rows.append(line.split())

        if len(rows) != self.ntrain:
            raise FileReadError(
                f"The [{block_name}] block of {self.path} holds {len(rows)} row(s), "
                f"but its header says the model has {self.ntrain} training point(s). "
                "The file is truncated or its header does not describe its contents."
            )

        block = np.empty((self.ntrain, ncols))
        for i, row in enumerate(rows):
            if len(row) != ncols:
                raise FileReadError(
                    f"Row {i + 1} of the [{block_name}] block of {self.path} holds "
                    f"{len(row)} value(s), but {ncols} were expected."
                )
            try:
                block[i, :] = [float(value) for value in row]
            except ValueError as error:
                raise FileReadError(
                    f"Row {i + 1} of the [{block_name}] block of {self.path} could "
                    f"not be read as {ncols} number(s): {error}"
                ) from error

        return block

    def _read_file(self, up_to: Optional[str] = None):
        """Read in a FEREBUS output file which contains the optimized
        hyperparameters, mean function, and other information that is needed to make predictions."""
        kernel_composition = ""
        kernel_dict = {}
        notes = {}

        stop_reading = False

        with open(self.path, "r") as f:
            for line in f:
                if stop_reading:
                    break

                if up_to is not None and up_to in line:
                    stop_reading = True

                if "<TODO>" in line:
                    continue

                if "program" in line:
                    self.program = self.program or line.split()[-1]
                    continue

                if "version" in line:
                    self.program_version = self.program_version or Version(
                        line.split()[-1]
                    )
                    continue

                if "jitter" in line or "nugget" in line or "noise" in line:
                    # noise to add to the diagonal to help with numerical stability.
                    # Typically on the scale 1e-6 to 1e-10
                    self.jitter = self.jitter or float(line.split()[-1])
                    continue

                if "likelihood" in line:
                    self.likelihood = self.likelihood or float(line.split()[-1])
                    continue

                if "#" in line and "=" in line:
                    line = line.lstrip("#")
                    key, val = line.split("=")
                    notes[key.strip()] = val.strip()
                    continue

                if line.startswith("#"):
                    line = line.lstrip("#")
                    notes[line.strip()] = None

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
                        mean = ConstantMean(float(next(f).split()[1]))
                    elif mean_type == "zero":
                        mean = ZeroMean()
                    elif mean_type in ["linear", "quadratic"]:
                        beta = np.array([float(b) for b in next(f).split()[1:]])
                        xmin = np.array([float(x) for x in next(f).split()[1:]])
                        ymin = float(next(f).split()[-1])
                        if mean_type == "linear":
                            mean = LinearMean(beta, xmin, ymin)
                        elif mean_type == "quadratic":
                            mean = QuadraticMean(beta, xmin, ymin)

                    self.mean = self.mean or mean
                    continue

                if "composition" in line:
                    # which kernels were used to make the GP model.
                    # Different kernels can be specified for different input dimensions
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
                        active_dims = np.array([int(ad) - 1 for ad in line.split()[1:]])
                    else:
                        active_dims = np.arange(ndims)

                    if kernel_type == "rbf":
                        thetas = np.array([float(hp) for hp in next(f).split()[1:]])
                        kernel_dict[kernel_name] = RBF(
                            kernel_name, thetas, active_dims=active_dims
                        )
                    elif kernel_type in [
                        "rbf-cyclic",
                        "rbf-cylic",
                    ]:  # Due to typo in FEREBUS 7.0
                        thetas = np.array([float(hp) for hp in next(f).split()[1:]])
                        kernel_dict[kernel_name] = RBFCyclic(
                            kernel_name, thetas, active_dims=active_dims
                        )
                    elif kernel_type == "constant":
                        value = float(next(f).split()[-1])
                        kernel_dict[kernel_name] = ConstantKernel(
                            kernel_name, value, active_dims=active_dims
                        )
                    elif kernel_type == "periodic":
                        thetas = np.array([float(hp) for hp in next(f).split()[1:]])
                        kernel_dict[kernel_name] = PeriodicKernel(
                            kernel_name,
                            thetas,
                            np.full(thetas.shape, 2 * np.pi),
                            active_dims=active_dims,
                        )

                    continue

                if "units.x" in line:
                    self.input_units = self.input_units or line.split()[1:]

                if "units.y" in line:
                    self.output_unit = self.output_unit or line.split()[-1]

                # training inputs data
                if "[training_data.x]" in line:
                    self.x = self.x or self._read_data_block(
                        f, "training_data.x", self.nfeats
                    )
                    continue

                # training labels data
                if "[training_data.y]" in line:
                    self.y = self.y or self._read_data_block(f, "training_data.y", 1)
                    continue

                if "[weights]" in line:
                    self.weights = self.weights or self._read_data_block(
                        f, "weights", 1
                    )

        self.kernel = (
            self.kernel
            if self.kernel or not kernel_composition
            else KernelInterpreter(kernel_composition, kernel_dict).interpret()
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

        # make into a 2d array in case a 1d is passed in
        # add check here in case not called from predict method
        if x_test.ndim == 1:
            x_test = x_test[np.newaxis, ...]

        return self.kernel.r(self.x, x_test)

    @property
    def R(self) -> np.ndarray:
        """Returns the covariance matrix and adds a jitter
        to the diagonal for numerical stability. This jitter is a very
        small number on the order of 1e-6 to 1e-10."""
        return self.kernel.R(self.x) + (self.jitter * np.identity(self.ntrain))

    @property
    def invR(self) -> np.ndarray:
        """Returns the inverse of the covariance matrix R"""
        return np.linalg.inv(self.R)

    @property
    def lower_cholesky(self) -> np.ndarray:
        """Decomposes the covariance matrix into L and L^T. Returns the lower triangular matrix L."""
        return np.linalg.cholesky(self.R)

    @property
    def _y_minus_mean(self):
        return self.y - self.mean.value(self.x).reshape((-1, 1))

    @property
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

        # make into a 2d array in case a 1d is passed in
        if x_test.ndim == 1:
            x_test = x_test[np.newaxis, ...]

        return (
            self.mean.value(x_test) + np.dot(self.r(x_test).T, self.weights)[:, -1]
        ).flatten()

    def variance(self, x_test: np.ndarray) -> np.ndarray:
        """Return the variance for the test data points."""
        train_test_covar = self.r(x_test)
        # temporary matrix, see Rasmussen Williams page 19 algo. 2.1
        v = np.linalg.solve(self.lower_cholesky, train_test_covar)

        # only the diagonal of v^T v is wanted, so it is summed column by column
        # rather than by forming the whole n_test by n_test matrix and throwing all
        # but its diagonal away (which costs n_test times as much time and memory)
        # TODO: need to multiply by tau^2 in order to get "true" variance which can be used for error estimations.
        # here it can only be used to compare points to figure out which point has the largest variance.
        return 1.0 - np.einsum("ij,ij->j", v, v)

    def _write_file(self, path: Path) -> None:
        if not path.parent.exists():
            mkdir(path.parent)
        if path.is_dir():
            path = (
                path
                / f"{self.system_name}_{self.prop}_{self.atom_name}{Model.get_filetype()}"
            )

        # these are so that the writing of models does not crash. They do not affect predictions
        if not self.jitter:
            self.jitter = 1e-6
        if not self.likelihood:
            self.likelihood = 1.0
        if not self.notes:
            self.notes = {}

        write_str = ""

        write_str += "# [metadata]\n"
        write_str += f"# program {self.program}\n"
        write_str += f"# version {self.program_version}\n"
        write_str += f"# jitter {self.jitter}\n"
        write_str += f"# likelihood {self.likelihood}\n"
        for key, val in self.notes.items():
            write_str += f"# {key} = {val}\n"
        write_str += "\n"
        write_str += "[system]\n"
        write_str += f"name {self.system_name}\n"
        write_str += f"atom {self.atom_name}\n"
        write_str += f"property {self.prop}\n"
        write_str += f"ALF {self.alf[0] + 1} {self.alf[1] + 1} {self.alf[2] + 1}\n"
        write_str += "\n"
        write_str += "[dimensions]\n"
        write_str += f"number_of_atoms {self.natoms}\n"
        write_str += f"number_of_features {self.nfeats}\n"
        write_str += f"number_of_training_points {self.ntrain}\n"
        write_str += "\n"
        write_str += self.mean.write_str()
        write_str += "\n"
        write_str += "[kernels]\n"
        write_str += f"number_of_kernels {self.kernel.nkernel}\n"
        write_str += f"composition {self.kernel.name}\n"
        write_str += "\n"
        write_str += self.kernel.write_str()
        write_str += "\n"
        write_str += "[training_data]\n"
        write_str += f"units.x {' '.join(self.input_units)}\n"
        write_str += f"units.y {self.output_unit}\n"
        write_str += "scaling.x none\n"
        write_str += "scaling.y none\n"
        write_str += "\n"
        write_str += "[training_data.x]\n"
        for xi in self.x:
            write_str += f"{' '.join(map(str, xi))}\n"
        write_str += "\n"
        write_str += "[training_data.y]\n"
        write_str += "\n".join(map(str, self.y.flatten()))
        write_str += "\n\n"
        write_str += "[weights]\n"
        write_str += "\n".join(map(str, self.weights.flatten()))
        write_str += "\n"

        return write_str

    def __repr__(self):
        return f"{self.__class__.__name__}(system={self.system_name}, atom={self.atom_name}, type={self.prop})"
