import numpy as np
from typing import List

def spherical_to_cartesian(r, theta, phi) -> List[float]:
    """
    Spherical to cartesian transformation, where r ∈ [0, ∞), θ ∈ [0, π], φ ∈ [-π, π).
        x = rsinθcosϕ
        y = rsinθsinϕ
        z = rcosθ
    """
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(phi) * np.sin(theta)
    z = r * np.cos(theta)
    return [x, y, z]
