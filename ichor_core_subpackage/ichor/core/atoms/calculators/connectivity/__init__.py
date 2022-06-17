from ichor.core.atoms.calculators.connectivity.distance import \
    calculate_connectivity_distance
from ichor.core.atoms.calculators.connectivity.valence import \
    calculate_connectivity_valence

connectivity_calculators = {
    "distance": calculate_connectivity_distance,
    "valence": calculate_connectivity_valence,
}

calculate_connectivity = connectivity_calculators["valence"]
