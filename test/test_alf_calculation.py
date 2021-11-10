import unittest
import sys
sys.path.append("../ichor/")
from ichor.files import Trajectory
from pathlib import Path
import os
import numpy as np

class TestALFCalculations(unittest.TestCase):
    
    """ These are tests to check if the ALF calculation matches the alf calculation done by hand (as determined by Cahn–Ingold–Prelog priority rules). The
    ALF that is calculated here is zero indexed because this allows us to correctly index the atoms in Python. Otherwise, the actual atom names start at index 1,
    so C1, C2, H3, etc.
    
    .. note::
        The numbers in the alf calculation can change because the atom's indices are determined by their ordering in the xyz file. Thus, a different ordering
        of the atoms in the xyz can result in the same structure, but the calculated alf will be different.
    """
    
    def test_water_monomer_alf(self):
        
        water_geometry_location = Path("test/test_geometries/test_water_monomer_geometry.xyz")
        traj = Trajectory(water_geometry_location)
        alf = traj.alf
        
        correct_alf = np.array([[0, 1, 2], [1, 0, 2], [2, 0, 1]])
        np.testing.assert_array_equal(alf.shape, correct_alf.shape)
        np.testing.assert_equal(alf, correct_alf)


    def test_methanol_alf(self):
        
        methanol_geometry_location = Path("test/test_geometries/test_methanol_geometry.xyz")
        traj = Trajectory(methanol_geometry_location)
        alf = traj.alf
        
        correct_alf = np.array([[0, 2, 1], [1, 0, 2], [2, 0, 5], [3, 0, 2], [4, 0, 2], [5, 2, 0]])
        np.testing.assert_array_equal(alf.shape, correct_alf.shape)
        np.testing.assert_equal(alf, correct_alf)  

    def test_water_dimer_alf(self):
        
        water_dimer_test_geometry_location = Path("test/test_geometries/test_water_dimer_geometry.xyz")
        traj = Trajectory(water_dimer_test_geometry_location)
        alf = traj.alf
        
        correct_alf = np.array([[0, 1, 2], [1, 0, 2], [2, 0, 1], [3, 4, 5], [4, 3, 5], [5, 3, 4]])
        np.testing.assert_array_equal(alf.shape, correct_alf.shape)
        np.testing.assert_equal(alf, correct_alf)


    def test_ammonia_alf(self):
        
        ammonia_test_geometry_location = Path("test/test_geometries/test_ammonia_geometry.xyz")
        traj = Trajectory(ammonia_test_geometry_location)
        alf = traj.alf
        
        correct_alf = np.array([[0, 1, 2], [1, 0, 2], [2, 0, 1], [3, 0, 1]])
        np.testing.assert_array_equal(alf.shape, correct_alf.shape)
        np.testing.assert_equal(alf, correct_alf)

    def test_glycine_alf(self):
        
        glycine_test_geometry_location = Path("test/test_geometries/test_glycine_geometry.xyz")
        traj = Trajectory(glycine_test_geometry_location)
        alf = traj.alf
        
        correct_alf = np.array([[0, 1, 3], [1, 5, 0], [2, 0, 1], [3, 6, 7], [4, 0, 1], [5, 9, 1], [6, 3, 7], [7, 3, 8], [8, 7, 11], [9, 5, 1],
                                [10, 5, 14], [11, 8, 7], [12, 8, 7], [13, 8, 7], [14, 10, 5], [15, 10, 5], [16, 10, 5], [17, 1, 5], [18, 7, 3]])
        np.testing.assert_array_equal(alf.shape, correct_alf.shape)
        np.testing.assert_equal(alf, correct_alf)

    def test_nma_alf(self):
        
        nma_test_geometry_location = Path("test/test_geometries/test_nma_geometry.xyz")
        traj = Trajectory(nma_test_geometry_location)
        alf = traj.alf
        
        correct_alf = np.array([[0, 1, 2], [1, 5, 6], [2, 0, 1], [3, 0, 1], [4, 0, 1], [5, 1, 6], [6, 1, 7], [7, 6, 8],
                                [8, 7, 6], [9, 7, 6], [10, 7 , 6], [11, 6, 1]])
        np.testing.assert_array_equal(alf.shape, correct_alf.shape)
        np.testing.assert_equal(alf, correct_alf)

if __name__ == "__main__":

    unittest.main()