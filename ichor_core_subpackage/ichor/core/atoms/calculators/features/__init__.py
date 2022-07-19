from typing import Callable
from typing import Dict


from ichor.core.atoms.calculators.features.alf_features import calculate_alf_features
from ichor.core.atoms.calculators.alf.alf import ALF

feature_calculators: Dict[str, Callable] = {
    "alf": calculate_alf_features
}

default_feature_calculator = feature_calculators["alf"]