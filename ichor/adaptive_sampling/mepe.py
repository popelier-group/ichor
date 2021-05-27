import json
from typing import Dict

import numpy as np
import numpy.linalg as la
from scipy.spatial.distance import cdist

from ichor.adaptive_sampling.expected_improvement import ExpectedImprovement
from ichor.atoms import ListOfAtoms
from ichor.models import Model, ModelsResult


def B(model: Model) -> float:
    return np.matmul(
        (
            la.inv(
                np.matmul(
                    np.matmul(np.ones((1, model.ntrain)), model.invR),
                    np.ones((model.ntrain, 1)),
                )
            )
        ),
        np.matmul(np.matmul(np.ones((1, model.ntrain)), model.invR), model.y),
    ).item()


def H(ntrain: int) -> np.ndarray:
    return np.matmul(
        np.ones((ntrain, 1)),
        la.inv(np.matmul(np.ones((1, ntrain)), np.ones((ntrain, 1)))).item()
        * np.ones((1, ntrain)),
    )


def cross_validation(model: Model) -> np.ndarray:
    d = (model.y - B(model)).reshape((-1, 1))
    h = H(model.ntrain)

    cross_validation_error = np.empty(model.ntrain)
    for i in range(model.ntrain):
        cross_validation_error[i] = (
            np.matmul(
                model.invR[i, :],
                (d + (d[i] / h[i][i]) * h[:][i].reshape((-1, 1))),
            )
            / model.invR[i][i]
        ).item() ** 2
    return cross_validation_error


# def closest_point(point, model) -> int:


class MEPE(ExpectedImprovement):
    def __init__(self, models):
        ExpectedImprovement.__init__(self, models)

    def cv_error(self, x: Dict[str, np.ndarray]) -> ModelsResult:
        cv_errors = ModelsResult()
        for atom in self.models.atoms:
            atom_cv_errors = ModelsResult()
            for model in self.models[atom]:
                cv = cross_validation(model)
                distances = cdist(x[model.atom], model.x)
                atom_cv_errors[model.type] = cv[distances.argmin(axis=-1,)]
            cv_errors[atom] = atom_cv_errors
        return cv_errors

    def alpha(self) -> float:
        from ichor.globals import GLOBALS

        cv_errors_file = GLOBALS.FILE_STRUCTURE["cv_errors"]
        if not cv_errors_file.exists():
            return 0.5

        with open(cv_errors_file, "r") as f:
            obj = json.load(f)
            npoints = obj["added_points"]
            cv_errors = ModelsResult(obj["cv_errors"])
            predictions = ModelsResult(obj["predictions"])

        alpha_sum = 0.0
        nalpha = 0
        for atom, data in predictions.items():
            for property, predicted_values in data.items():
                true_values = self.models[atom][property].y[-npoints:]
                true_error = (true_values - predicted_values) ** 2
                alpha_sum += np.sum(
                    0.99
                    * np.clip(
                        0.5 * true_error / np.array(cv_errors[atom][property]),
                        0.0,
                        1.0,
                    )
                )
                nalpha += len(true_values)
        return alpha_sum / nalpha

    def __call__(self, points: ListOfAtoms, npoints: int) -> np.ndarray:
        features_dict = self.models.get_features_dict(points)
        cv_errors = self.cv_error(features_dict)
        variance = self.models.variance(features_dict)
        alpha = self.alpha()
        epe = alpha * cv_errors - (1.0 - alpha) * variance

        epe = np.flip(np.argsort(epe.reduce(-1)), axis=-1)[:npoints]

        from ichor.globals import GLOBALS

        with open(GLOBALS.FILE_STRUCTURE["cv_errors"], "w") as f:
            json.dump(
                {
                    "added_points": npoints,
                    "cv_errors": cv_errors[epe].to_list(),
                    "predictions": self.models.predict(features_dict)[
                        epe
                    ].to_list(),
                },
                f,
            )

        return epe
