from typing import List

import numpy as np


def spherical_to_cartesian(r, theta, phi) -> List[float]:
    """
    Spherical to cartesian transformation, where r in [0, \inf), \theta in [0, \pi], \phi in [-\pi, \pi).
        x = r sin \theta cos\phi
        y = r sin \phi sin\theta
        z = r cos\theta
    """
    x = r * np.sin(theta) * np.cos(phi)
    y = r * np.sin(phi) * np.sin(theta)
    z = r * np.cos(theta)
    return [x, y, z]
