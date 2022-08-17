from typing import Callable
from typing import Dict


from ichor.core.calculators.features.alf_features_calculator import calculate_alf_features

feature_calculators: Dict[str, Callable] = {
    "alf": calculate_alf_features
}

default_feature_calculator = feature_calculators["alf"]