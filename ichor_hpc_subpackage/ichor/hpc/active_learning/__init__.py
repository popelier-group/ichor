from ichor.hpc import GLOBALS
from ichor.hpc.active_learning.active_learning_method import \
    ActiveLearningMethod
from ichor.hpc.active_learning.highest_variance import HighestVariance
# import active learning methods to be accessed in locals()
from ichor.hpc.active_learning.mepe import MEPE
from ichor.hpc.active_learning.random_sampling import RandomSampling
from ichor.hpc.active_learning.sigmu import SigMu
from ichor.hpc.active_learning.uncertainty_query import UncertaintyQuery

# get a dictionary of key:value pairs of the active learning method name : active learning method class
active_learning_methods = {
    active_learning_method.name: active_learning_method
    for active_learning_method in locals().values()
    if isinstance(active_learning_method, type)
    and issubclass(active_learning_method, ActiveLearningMethod)
    and active_learning_method is not ActiveLearningMethod
}

learning_method_cls = active_learning_methods[GLOBALS.ACTIVE_LEARNING_METHOD]
