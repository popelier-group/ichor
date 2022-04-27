from ichor_lib.units import Angle, degrees_to_radians

from typing import Optional
import numpy as np


def mag(x: np.ndarray) -> float:
    """
    Calculates the magnitude of vector x
    :param x: vector of length n
    :return: the magnitude of vector x as float
    """
    return np.sqrt(x.dot(x))


def Rx(rx: float, units: Optional[Angle] = Angle.Radians) -> np.ndarray:
    if units is Angle.Degrees:
        rx = degrees_to_radians(rx)
    return np.array([
        [1, 0, 0],
        [0, np.cos(rx), -np.sin(rx)],
        [0, np.sin(rx), np.cos(rx)],
    ])


def Ry(ry: float, units: Optional[Angle] = Angle.Radians) -> np.ndarray:
    if units is Angle.Degrees:
        ry = degrees_to_radians(ry)
    return np.array([
        [np.cos(ry), 0, np.sin(ry)],
        [0, 1, 0],
        [-np.sin(ry), 0, np.cos(ry)],
    ])


def Rz(rz: float, units: Optional[Angle] = Angle.Radians) -> np.ndarray:
    if units is Angle.Degrees:
        rz = degrees_to_radians(rz)
    return np.array([
        [np.cos(rz), -np.sin(rz), 0],
        [np.sin(rz), np.cos(rz), 0],
        [0, 0, 1],
    ])


def get_plane(a, b, c):
    ab = b-a
    ac = c-a

    n = np.cross(ab, ac)

    p1 = n[0]
    p2 = n[1]
    p3 = n[2]
    p4 = -ab[0]*n[0]-ab[1]*n[1]*ab[2]*n[2]
    return p1, p2, p3, p4


# Function to mirror image
def mirror_point(plane, p):
    a, b, c, d = plane

    x1 = p[:,0]
    y1 = p[:,1]
    z1 = p[:,2]

    k =(-a * x1-b * y1-c * z1-d)/float((a * a + b * b + c * c))
    x2 = a * k + x1
    y2 = b * k + y1
    z2 = c * k + z1
    x3 = 2 * x2-x1
    y3 = 2 * y2-y1
    z3 = 2 * z2-z1

    p[:,0] = x3
    p[:,1] = y3
    p[:,2] = z3
    return p
