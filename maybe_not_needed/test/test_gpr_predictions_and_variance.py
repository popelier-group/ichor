import unittest
import sys
sys.path.append("../ichor/")
import numpy as np
import pandas as pd
from pathlib import Path
from ichor.ichor_lib.models import Model

class TestGPRPredictions(unittest.TestCase):
    
    """ Tests to check if the GPR model predictions and variance are of the correct shape. Also checks if the predictions made by ichor
    match (or are close to) predictions made previously with ichor.
    
    .. note::
        At the moment only O1 predictions and variance is tested, the H2 and H3 model files and test sets are not used (but are in the testing directory
        in case they are needed for something in the future)
    """
    
    def test_water_monomer_iqa_predictions(self):
        
        data_path = Path("test/test_gpr_models/water_monomer/test_set/O1_features_with_properties.txt")
        dataset = pd.read_csv(data_path, index_col=None, header=0).values
        test_x = dataset[:, :3]  # get the features of the dataset
        np.testing.assert_equal(test_x.shape, (500, 3))  # we have 500 test points in the test dataset
        test_y = dataset[:, -1]  # get the iqa energies for the points
        np.testing.assert_equal(test_y.shape, (500,))  # we have 500 test points in the test dataset
        # load O1 model file
        model_path = Path("test/test_gpr_models/water_monomer/models/WATER_MONOMER_iqa_O1.model")
        model = Model(model_path)
        predictions = model.predict(test_x)
        np.testing.assert_equal(predictions.shape, (500,))  # we have 500 test points in the test dataset
        previous_predictions = np.loadtxt(Path("test/test_gpr_models/water_monomer/previous_gpr_predictions/o1_predictions.txt"))
        np.testing.assert_allclose(predictions, previous_predictions)
    
    def test_water_monomer_variance(self):
        
        data_path = Path("test/test_gpr_models/water_monomer/test_set/O1_features_with_properties.txt")
        
        dataset = pd.read_csv(data_path, index_col=None, header=0).values
        test_x = dataset[:, :3]  # get the features of the dataset
        np.testing.assert_equal(test_x.shape, (500, 3))  # we have 500 test points in the test dataset
        test_y = dataset[:, -1]  # get the iqa energies for the points
        np.testing.assert_equal(test_y.shape, (500,))  # we have 500 test points in the test dataset
        
        # load O1 model file
        model_path = Path("test/test_gpr_models/water_monomer/models/WATER_MONOMER_iqa_O1.model")
        model = Model(model_path)
        test_set_variance = model.variance(test_x)
        np.testing.assert_equal(test_set_variance.shape, (500,))
        
        previous_variance = np.loadtxt(Path("test/test_gpr_models/water_monomer/previous_gpr_predictions/o1_variance.txt"))
        np.testing.assert_allclose(test_set_variance, previous_variance)
        
    def test_ammonia_N1_iqa_predictions(self):
        
        data_path = Path("test/test_gpr_models/ammonia/test_set/N1_features_with_properties.csv")
        dataset = pd.read_csv(data_path, index_col=None, header=0).values
        test_x = dataset[:, :6]  # get the features of the dataset
        np.testing.assert_equal(test_x.shape, (500, 6))  # we have 500 test points in the test dataset, 6 features
        test_y = dataset[:, 7]  # get the iqa energies for the points
        np.testing.assert_equal(test_y.shape, (500,))  # we have 500 test points in the test dataset

        model_path = Path("test/test_gpr_models/ammonia/models/AMMONIA_iqa_N1.model")
        model = Model(model_path)
        predictions = model.predict(test_x)
        np.testing.assert_equal(predictions.shape, (500,))  # we have 500 test points in the test dataset
        previous_predictions = np.loadtxt(Path("test/test_gpr_models/ammonia/previous_gpr_predictions/n1_predictions.txt"))
        np.testing.assert_allclose(predictions, previous_predictions)
        
        variance = model.variance(test_x)
        np.testing.assert_equal(variance.shape, (500,))  # we have 500 test points in the test dataset
        previous_variance = np.loadtxt(Path("test/test_gpr_models/ammonia/previous_gpr_predictions/n1_variance.txt"))
        np.testing.assert_allclose(variance, previous_variance)
        
if __name__ == "__main__":

    unittest.main()