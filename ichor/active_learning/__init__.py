from ichor.active_learning.expected_improvement import ExpectedImprovement
from ichor.active_learning.mepe import MEPE
from ichor.common.functools import lazy

active_learning_methods = {
    active_learning_method.name: active_learning_method
    for active_learning_method in locals()
    if isinstance(active_learning_method, ExpectedImprovement)
}


# implemented as a lazy function to prevent circular dependency
@lazy
def _get_active_learning_method() -> ExpectedImprovement:
    from ichor.globals import GLOBALS

    return active_learning_methods[GLOBALS.ACTIVE_LEARNING_METHOD]


ActiveLearningMethod = _get_active_learning_method()

__all__ = ["ActiveLearningMethod"]
