from ichor.hpc.make_sets.min_max import MinMax
from ichor.hpc.make_sets.min_max_mean import MinMaxMean
from ichor.hpc.make_sets.random_points import RandomPoints

MAKE_SET_METHODS_DICT = {
    "min_max_mean": MinMaxMean,
    "min_max": MinMax,
    "random": RandomPoints
}