from typing import Dict

from ichor.core.atoms.calculators.features.alf import (
    calculate_alf_features, get_alf_feature_calculator)
from ichor.core.atoms.calculators.features.features import \
    FeatureCalculatorFunction

feature_calculators: Dict[str, FeatureCalculatorFunction] = {
    "alf": calculate_alf_features
}

default_feature_calculator = feature_calculators["alf"]
