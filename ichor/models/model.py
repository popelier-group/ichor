from pathlib import Path
import numpy as np


class Model:

    """ one model file (grouped by the Models class)"""

    def __init__(self, fname, read=False):
        self.fname = Path(fname)

        self.directory = ""
        self.basename = ""

        self.system_name = ""
        self.type = ""
        self.atom = ""
        self.atom_number = ""
        self.legacy = False

        self.analyse_name()

        # TODO: Convert these to lowercase
        self.n_train = 0
        self.n_feats = 0

        self.mu = 0
        self.sigma2 = 0

        self.normalise = False
        self.norm_min = []
        self.norm_max = [] # convert to numpy arrays when initialized, use type annotations

        # self.training_dataset = Dataset()

        self.standardise = False
        self.xmu = []
        self.xstd = []
        self.ymu = []
        self.ystd = []

        self.has_cyclic_kernel = False
        self.kernel = None
        self.kernel_list = {}

        self.weights = []

        self.y = []
        self.X = []
        if read and self.fname:
            self.read()
            # if self.normalise:
            #     self.X = self.normalise_data(self.X)
            # elif self.standardise:
            #     self.X = self.standardise_data(self.y)

    def normalise_data(self, data):
        for i in range(self.n_feats):
            self.norm_min.append(data[:, i].min(0))
            self.norm_max.append(data[:, i].max(0))
            data[:, i] = (data[:, i] - data[:, i].min(0)) / data[:, i].ptp(0)
        self.norm_min = np.array(self.norm_min)
        self.norm_max = np.array(self.norm_max)
        return data

    def normalise_array(self, array):
        return (array - self.norm_min) / (self.norm_max - self.norm_min)

    def standardise_array(self, array, mu, std):
        return (array - mu) / std

    @property
    def num(self):
        return int(self.atom_number)

    @property
    def i(self):
        return self.num - 1

    def read(self, up_to=None):
        if self.n_train > 0:
            return
        if self.legacy:
            self.read_legacy(up_to)
        else:
            self.read_updated(up_to)

    def read_legacy(self, up_to):
        with open(self.fname) as f:
            for line in f:
                if "norm" in line:
                    self.normalise = True
                if "stand" in line:
                    self.standardise = True
                if "Feature" in line:
                    self.n_feats = int(line.split()[1])
                if "Number_of_training_points" in line:
                    self.n_train = int(line.split()[1])
                if "Mu" in line:
                    numbers = line.split()
                    self.mu = float(numbers[1])
                    self.sigma2 = float(numbers[3])
                if "Theta" in line:
                    line = next(f)
                    hyper_parameters = []
                    while ";" not in line:
                        hyper_parameters.append(float(line))
                        line = next(f)
                    self.kernel = RBFCyclic(np.array(hyper_parameters))
                if "Weights" in line:
                    line = next(f)
                    while ";" not in line:
                        self.weights.append(float(line))
                        line = next(f)
                    self.weights = np.array(self.weights)
                if "Property_value_Kriging_centers" in line:
                    line = next(f)
                    while "training_data" not in line:
                        self.y.append(float(line))
                        line = next(f)
                    self.y = np.array(self.y).reshape((-1, 1))
                if "training_data" in line:
                    line = next(f)
                    while ";" not in line:
                        self.X.append([float(num) for num in line.split()])
                        line = next(f)
                    self.X = np.array(self.X).reshape(
                        (self.n_train, self.n_feats)
                    )

                if up_to is not None and up_to in line:
                    break

    def read_updated(self, up_to):
        with open(self.fname) as f:
            for line in f:
                if line.startswith("#"):
                    continue

                if "name" in line:
                    self.system_name = line.split()[1]
                    continue
                if "property" in line:
                    self.type = line.split()[1]
                    continue
                if line.startswith("atom"):
                    self.atom = line.split()[1]
                    continue

                if "number_of_features" in line:
                    self.n_feats = int(line.split()[1])
                if "number_of_training_points" in line:
                    self.n_train = int(line.split()[1])

                if "[mean]" in line:
                    line = next(f)
                    line = next(f)
                    self.mu = float(line.split()[1])

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
                        self.kernel_list[kernel_name] = RBF(lengthscale)
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
                        self.kernel_list[kernel_name] = RBFCyclic(lengthscale)
                        self.has_cyclic_kernel = True
                    elif kernel_type == "constant":
                        line = next(f)
                        line = next(f)
                        line = next(f)
                        value = float(line.split()[-1])
                        self.kernel_list[kernel_name] = Constant(value)

                if "scaling.x" in line:
                    scaling = line.split()[-1].strip()
                    if scaling == "standardise":
                        self.standardise = True

                if "[training_data.x]" in line:
                    line = next(f)
                    while line.strip() != "":
                        self.X.append([float(num) for num in line.split()])
                        line = next(f)

                if "[training_data.y]" in line:
                    line = next(f)
                    while line.strip() != "":
                        self.y.append(float(line))
                        line = next(f)

                if "[weights]" in line:
                    line = next(f)
                    while line.strip() != "":
                        self.weights.append(float(line))
                        try:
                            line = next(f)
                        except:
                            break

                if up_to is not None and up_to in line:
                    break

        self.X = np.array(self.X)
        self.y = np.array(self.y).reshape((-1, 1))

        if self.standardise:
            self.xmu = np.mean(self.X, axis=0)
            self.xstd = np.std(self.X, axis=0)
            self.ymu = np.mean(self.y, axis=0)
            self.ystd = np.std(self.y, axis=0)

            self.X = self.standardise_array(self.X, self.xmu, self.xstd)
            self.y = self.standardise_array(self.y, self.ymu, self.ystd)

            for kernel_name, kernel in self.kernel_list.items():
                if isinstance(kernel, (RBFCyclic)):
                    kernel.xstd = self.xstd

        self.kernel = KernelInterpreter(
            kernel_composition, self.kernel_list
        ).interpret()
        self.weights = np.array(self.weights)

    def write(self, directory=None, legacy=False):
        directory = (
            Path(GLOBALS.FILE_STRUCTURE["models"])
            if not directory
            else Path(directory)
        )
        if self.legacy or legacy:
            self.write_legacy(directory)
        else:
            self.write_updated(directory)

    def write_legacy(self, directory):
        atom_num = self.atom_number.zfill(2)
        model_type = self.type.upper() if self.type == "iqa" else self.type
        fname = Path(f"{self.system_name}_kriging_{model_type}_{atom_num}.txt")
        path = directory / fname
        with open(path, "w") as f:
            f.write("Kriging Results and Parameters\n")
            f.write(";\n")
            f.write(f"Feature {self.n_feats}\n")
            f.write(f"Number_of_training_points {self.n_train}\n")
            f.write(";\n")
            f.write(f"Mu {self.mu} Sigma_Squared {self.sigma2}\n")
            f.write(";\n")
            f.write("Theta\n")
            for theta in self.kernel.params:
                f.write(f"{theta}\n")
            f.write(";\n")
            f.write("p\n")
            for _ in range(len(self.kernel.params)):
                f.write("2.00000000000000\n")
            f.write(";\n")
            f.write("Weights\n")
            for weight in self.weights:
                f.write(f"{weight}\n")
            f.write(";\n")
            f.write("R_matrix\n")
            f.write(f"Dimension {self.n_train}\n")
            f.write(";\n")
            f.write("Property_value_Kriging_centers\n")
            for y in self.y:
                f.write(f"{y[0]}\n")
            f.write("training_data\n")
            for x in self.X:
                for i in range(0, len(x), 3):
                    f.write(f"{x[i]} {x[i+1]} {x[i+2]}\n")
            f.write(";\n")

    def write_updated(self, directory):
        UsefulTools.not_implemented()

    def analyse_name(self):
        self.directory = self.fname.parent
        self.basename = self.fname.name

        fname_split = self.fname.stem.split("_")

        if self.fname.suffix == ".txt":
            self.system_name = fname_split[0]
            self.type = fname_split[2].lower()
            self.atom_number = fname_split[3]
            self.legacy = True
        elif self.fname.suffix == ".model":
            self.system_name = fname_split[0]
            self.type = fname_split[1]
            self.atom = fname_split[2]
            self.atom_number = re.findall("\d+", self.atom)[0]
            self.legacy = False
        else:
            # TODO: Convert to fatal error
            printq(f"ERROR: Unknown Model Type {self.fname.suffix}")

    def remove_no_noise(self):
        no_noise_line = -1
        data = []
        with open(self.fname, "r") as f:
            for i, line in enumerate(f):
                if "No_Noise" in line:
                    no_noise_line = i
                    f.seek(0)
                    data = f.readlines()
                    break
                if i > 10:
                    break
        if data and no_noise_line > 0:
            del data[no_noise_line]
            with open(self.fname, "w") as f:
                f.writelines(data)

    def get_fname(self, directory=None):
        if directory is None:
            directory = Path(self.directory)
        if self.legacy:
            basename = Path(
                f"{self.system_name}_kriging_{self.type}_{self.atom_number}.txt"
            )
        else:
            basename = Path(
                f"{self.system_name}_{self.type}_{self.atom}.model"
            )
        return directory / basename

    def copy_to_log(self):
        log_directory = Path(GLOBALS.FILE_STRUCTURE["log"])
        FileTools.mkdir(log_directory)

        if self.n_train == 0:
            if self.legacy:
                self.read(up_to="number_of_training_points")
            else:
                self.read(up_to="Number_of_training_points")

        n_train = str(self.n_train).zfill(4)
        log_directory /= Path(f"{self.system_name}{n_train}")
        FileTools.mkdir(log_directory)
        log_model_file = self.get_fname(log_directory)

        FileTools.copy_file(self.fname, log_model_file)

    def r(self, features):
        if self.standardise:
            return self.kernel.r(
                self.standardise_array(features, self.xmu, self.xstd), self.X
            )
        else:
            return self.kernel.r(features, self.X)
        # return numba_r_rbf(features, self.X, np.array(self.hyper_parameters))

    @property
    # TODO: @cached
    def R(self):
        try:
            return self._R
        except AttributeError:
            self._R = self.kernel.R(self.X)
            # self._R = numba_R_rbf(self.X, np.array(self.hyper_parameters))
            return self._R

    def add_nugget(self, nugget=1e-12):
        return self.R + np.eye(self.n_train) * nugget

    @property
    def invR(self):
        try:
            return self._invR
        except AttributeError:
            try:
                self._invR = la.inv(self.R)
            except:
                nugget = float(GLOBALS.FEREBUS_NUGGET)
                oom = 0
                while nugget < float(GLOBALS.MAX_NUGGET):
                    nugget = GLOBALS.FEREBUS_NUGGET * 10 ** oom
                    R = self.add_nugget(nugget)
                    logger.warning(
                        f"Singular Matrix Encountered: Nugget of {nugget}  used on model {self.fname}:{self.n_train}"
                    )
                    try:
                        self._invR = la.inv(R)
                        break
                    except la.LinAlgError:
                        if nugget <= float(GLOBALS.MAX_NUGGET):
                            logger.error(
                                f"Could not invert R Matrix of {self.fname}:{self.n_Train}: Singular Matrix Encountered"
                            )
                            sys.exit(1)
                        oom += 1
            return self._invR

    @property
    def ones(self):
        try:
            return self._ones
        except AttributeError:
            self._ones = np.ones((self.n_train, 1))
            return self._ones

    @property
    def H(self):
        try:
            return self._H
        except AttributeError:
            self._H = np.matmul(
                self.ones,
                la.inv(np.matmul(self.ones.T, self.ones)).item() * self.ones.T,
            )
            return self._H

    @property
    def B(self):
        try:
            return self._B
        except AttributeError:
            self._B = np.matmul(
                (
                    la.inv(
                        np.matmul(np.matmul(self.ones.T, self.invR), self.ones)
                    )
                ),
                np.matmul(np.matmul(self.ones.T, self.invR), self.y),
            ).item()
            return self._B

    @property
    def cross_validation(self):
        # TODO: move out of Model
        try:
            return self._cross_validation
        except AttributeError:
            d = self.y - self.B * self.ones

            self._cross_validation = []
            for i in range(self.n_train):
                cve = (
                    np.matmul(
                        self.invR[i, :],
                        (
                            d
                            + (d[i] / self.H[i][i])
                            * self.H[:][i].reshape((-1, 1))
                        ),
                    )
                    / self.invR[i][i]
                )
                self._cross_validation.append(cve.item() ** 2)
            return self._cross_validation

    def predict(self, point):
        # TODO: ntrain x nfeats matrix, make multiple predictions at once
        if isinstance(point, Point):
            features = point.features[self.i] #self.i = index of features
        else:
            features = point[self.i]
        r = self.r(features)
        weights = self.weights.reshape((-1, 1))
        prediction = self.mu + np.matmul(r.T, weights).item()
        if self.standardise:
            prediction = prediction * self.ystd.item() + self.ymu.item()
        return prediction

    def variance(self, point):
        # TODO: r is calcualted twice, once for predictions and once for variance
        r = self.r(point.features[self.i])

        res1 = np.matmul(r.T, np.matmul(self.invR, r))
        res2 = np.matmul(self.ones.T, np.matmul(self.invR, r))
        res3 = np.matmul(self.ones.T, np.matmul(self.invR, self.ones))

        return self.sigma2 * (
            1 - res1.item() + (1 + res2.item()) ** 2 / res3.item()
        )

    def distance_to_point(self, point):
        if self.standardise:
            point = np.array(
                self.standardise_array(
                    point.features[self.i], self.xmu, self.xstd
                )
            ).reshape((1, -1))
        else:
            point = np.array(point.features[self.i]).reshape((1, -1))
        if self.has_cyclic_kernel:
            if self.standardise:
                return standardised_cyclic_cdist(
                    point, np.array(self.X), np.array(self.xstd)
                )
            else:
                return cyclic_cdist(point, np.array(self.X))
        else:
            return distance.cdist(point, self.X)

    def closest_point(self, point):
        return self.distance_to_point(point).argmin()

    def cross_validation_error(self, point):
        closest_point = self.closest_point(point)
        return self.cross_validation[closest_point], closest_point

    def link(self, dst_dir, convert_to_legacy=False):
        if not self.legacy and convert_to_legacy:
            self.write_legacy(dst_dir)
        else:
            abs_path = os.path.abspath(self.fname)
            dst = os.path.join(dst_dir, self.basename)
            if os.path.exists(dst):
                os.remove(dst)
            else:
                try:
                    os.unlink(dst)
                except:
                    pass
            os.symlink(abs_path, dst)