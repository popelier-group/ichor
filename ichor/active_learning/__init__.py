from ichor.active_learning.expected_improvement import ExpectedImprovement
from ichor.active_learning.mepe import MEPE
from ichor.globals import GLOBALS

active_learning_methods = {
    active_learning_method.name: active_learning_method
    for active_learning_method in locals().values()
    if isinstance(active_learning_method, type)
    and issubclass(active_learning_method, ExpectedImprovement)
    and active_learning_method is not ExpectedImprovement
}

ActiveLearningMethod = active_learning_methods[GLOBALS.ACTIVE_LEARNING_METHOD]

__all__ = ["ActiveLearningMethod"]
