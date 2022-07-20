from typing import Callable
from typing import Dict


from ichor.core.calculators.features.alf_features import calculate_alf_features
from ichor.core.calculators.alf.alf import ALF

feature_calculators: Dict[str, Callable] = {
    "alf": calculate_alf_features
}

default_feature_calculator = feature_calculators["alf"]