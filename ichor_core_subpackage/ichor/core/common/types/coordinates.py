import numpy as np


class Coordinates3D:
    def __init__(self, x, y, z):
        self.coordinates = np.array([x, y, z], dtype=float)

    @property
    def x(self):
        return self.coordinates[0]

    @property
    def y(self):
        return self.coordinates[1]

    @property
    def z(self):
        return self.coordinates[2]
