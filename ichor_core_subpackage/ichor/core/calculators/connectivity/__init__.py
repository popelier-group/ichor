from typing import Dict, Callable

from ichor.core.calculators.connectivity.distance_connectivity_calculator import (
    connectivity_calculator_distance,
)
from ichor.core.calculators.connectivity.valence_connectivity_calculator import (
    connectivity_calculator_valence,
)

connectivity_calculators: Dict[str, Callable] = {
    "distance": connectivity_calculator_distance,
    "valence": connectivity_calculator_valence,
}

default_connectivity_calculator = connectivity_calculators["valence"]
