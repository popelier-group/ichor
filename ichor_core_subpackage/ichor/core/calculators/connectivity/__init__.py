from typing import Dict, Callable

from ichor.core.atoms.calculators.connectivity.distance import (
    default_connectivity_calculator_distance,
)
from ichor.core.atoms.calculators.connectivity.valence import (
    default_connectivity_calculator_valence,
)

connectivity_calculators: Dict[str, Callable] = {
    "distance": default_connectivity_calculator_distance,
    "valence": default_connectivity_calculator_valence,
}

default_connectivity_calculator = connectivity_calculators["valence"]
