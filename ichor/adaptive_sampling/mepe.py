from ichor.adaptive_sampling.expected_improvement import ExpectedImprovement
from typing import List
from ichor.atoms import ListOfAtoms
import numpy as np
from ichor.models import Model, ModelsResult
import numpy.linalg as la
from typing import Dict
from scipy.spatial.distance import cdist


def B(model: Model) -> float:
    return np.matmul(
        (
            la.inv(np.matmul(np.matmul(np.ones((1, model.ntrain)), model.invR), np.ones((model.ntrain, 1))))
        ),
        np.matmul(np.matmul(np.ones((1, model.ntrain)), model.invR), model.y),
    ).item()


def H(ntrain: int) -> np.ndarray:
    return np.matmul(
        np.ones((ntrain, 1)),
        la.inv(np.matmul(np.ones((1, ntrain)), np.ones((ntrain, 1)))).item() * np.ones((1, ntrain)),
    )


def cross_validation(model: Model) -> np.ndarray:
    d = (model.y - B(model)).reshape((-1, 1))
    h = H(model.ntrain)

    cross_validation_error = np.empty(model.ntrain)
    for i in range(model.ntrain):
        cross_validation_error[i] = (
                np.matmul(
                    model.invR[i, :],
                    (
                            d
                            + (d[i] / h[i][i])
                            * h[:][i].reshape((-1, 1))
                    ),
                )
                / model.invR[i][i]
        ).item() ** 2
    return cross_validation_error

# def closest_point(point, model) -> int:



class MEPE(ExpectedImprovement):
    def __init__(self, models):
        ExpectedImprovement.__init__(self, models)

        self.alpha = 0.5

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

    def __call__(self, points: ListOfAtoms) -> np.ndarray:
        features_dict = self.models.get_features_dict(points)
        epe = self.alpha*self.cv_error(features_dict) - (1.0-self.alpha)*self.models.variance(features_dict)
        return np.flip(np.argsort(epe.reduce(-1)), axis=-1)


