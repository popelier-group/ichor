from typing import Dict

from ichor.core.atoms.calculators.connectivity.distance import (
    calculate_connectivity_distance,
)
from ichor.core.atoms.calculators.connectivity.valence import (
    calculate_connectivity_valence,
)
from ichor.core.atoms.calculators.connectivity.connectivity import (
    ConnectivityCalculatorFunction,
)

connectivity_calculators: Dict[str, ConnectivityCalculatorFunction] = {
    "distance": calculate_connectivity_distance,
    "valence": calculate_connectivity_valence,
}

default_connectivity_calculator = connectivity_calculators["valence"]
