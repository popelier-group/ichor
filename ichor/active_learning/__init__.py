from ichor.active_learning.active_learning_method import ActiveLearningMethod
# import active learning methods to be accessed in locals()
from ichor.active_learning.mepe import MEPE
from ichor.active_learning.highest_variance import HighestVariance
from ichor.globals import GLOBALS

# get a dictionary of key:value pairs of the active learning method name : active learning method class
active_learning_methods = {
    active_learning_method.name: active_learning_method
    for active_learning_method in locals().values()
    if isinstance(active_learning_method, type)
    and issubclass(active_learning_method, ActiveLearningMethod)
    and active_learning_method is not ActiveLearningMethod
}

learning_method_cls = active_learning_methods[GLOBALS.ACTIVE_LEARNING_METHOD]

__all__ = ["learning_method_cls"]
