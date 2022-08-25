from pathlib import Path
from typing import List, Tuple, Dict, Union
from ichor.core.atoms import ListOfAtoms
from ichor.core.common.int import count_digits
from ichor.core.common.io import mkdir
from ichor.core.files import XYZ, PointsDirectory, Trajectory, PointDirectory
from ichor.hpc.make_sets import MAKE_SET_METHODS_DICT
from ichor.hpc import FILE_STRUCTURE

# makes all the sets at once, mutating the points_input, ensuring that each set has unique points.
# as a Path is passed in and not an object containing points, this mutation should not break code
# as objects containing points are made and used only inside the function.
def make_sets(
    points_input: Path,
    system_name: str,
    training_set_methods: Dict[str, Union[int, None]],
    sample_pool_methods: Dict[str, Union[int, None]],
    validation_set_methods: Dict[str, Union[int, None]],
    ):
    """Makes sets of points given a points input. The sets are guaranteed to contain unique points as
    the list of points that is made in the function is mutated to ensure that every point is added to one set
    and is added only once.

    :param points_input: A path to a file/directory containing Points
    :param training_set_methods: A dictionary of key:method name, value: number of points to add to be
        used to generate a training set. If None, default is {"random": 500}
    :param sample_pool_methods: A dictionary of key:method name, value: number of points to add to be
        used to generate a sample pool. If None, default is {"random": 10000}
    :param validation_set_methods: A dictionary of key:method name, value: number of points to add to be
        used to generate a validation set. If None, default is {"random": 500}
    :raises TypeError: If a file that cannot be read or does not contain points is passed in.
    """
    
    if points_input.suffix == ".xyz":
        points = Trajectory(points_input)
    elif points_input.is_dir():
        points = PointsDirectory(points_input)
    else:
        raise TypeError(
            f"Cannot convert path '{points_input}' into type 'ListOfAtoms'"
        )
    
    # use this later for when writing file names to correspond to the timestep in the trajectory
    for idx, p in enumerate(points):
        p._original_index = idx

    if not training_set_methods:
        training_set_methods = {"random": 500}
    if not sample_pool_methods:
        sample_pool_methods = {"random": 10000}
    if not validation_set_methods:
        validation_set_methods = {"random": 500}

    # check that there are enough points provided
    total_number_of_points_in_sets = sum(training_set_methods.values(), sample_pool_methods.values(), validation_set_methods.values())
    if total_number_of_points_in_sets > len(points):
        raise ValueError("The total number of points in the sets is greater than the number of supplied points in the trajectory/directory.")

    s = generate_geometries_set(points, training_set_methods)
    write_set_to_dir(FILE_STRUCTURE["training_set"], s, system_name)

    s = generate_geometries_set(points, sample_pool_methods)
    write_set_to_dir(FILE_STRUCTURE["sample_pool"], s, system_name)

    s = generate_geometries_set(points, validation_set_methods)
    write_set_to_dir(FILE_STRUCTURE["validation_set"], s, system_name)


def generate_geometries_set(points: "ListOfAtoms", methods: Dict[str, Union[int, None]]):
    total_set = []
    for method_name, number_of_points in methods.items():
        one_method_set = make_set(points, method_name, number_of_points)
        total_set += one_method_set
    return total_set

def make_set(
    all_points: "ListOfAtoms", method_name: str, npoints: int) -> List[Tuple[str, int]]:

    new_set = []
    # iterate over the possible classes
    for make_set_class_name, make_set_class in MAKE_SET_METHODS_DICT.items():
        # if the method matches the name of a class, then get the indices of points using that class
        if make_set_class_name == method_name:
            
            indices_list = make_set_class.get_points_indices(all_points, npoints)
            
            # get the indices from the ListOfAtoms instance and add not new set of points
            # mutate all_points to prevent duplicates.
            for idx in indices_list:
                # add instance of Atoms or PointDirectory to new set
                new_set.append(all_points[idx])
    
                del all_points[idx]
            
    if len(new_set) == 0:
        raise ValueError("The newly created set has length 0.")

    return new_set

def write_set_to_dir(path: Path, points: List[Tuple[str, int]], system_name: str) -> None:
    
    mkdir(path)
    for point in points:
        point_name = f"{system_name}{point._original_index}"
        mkdir(path / point_name)
        if isinstance(point, PointDirectory):
            xyz = XYZ(path / point_name / f"{point_name}{XYZ.filetype}", atoms=point.atoms)
        else:
            xyz = XYZ(path / point_name / f"{point_name}{XYZ.filetype}", atoms=point)
        # centering is needed because Gaussian wfn file writes out ****** instead of x,y,z coordinate
        # if x,y,z coordinate is greater than 100 (because they did not account for that....)
        xyz.atoms.centre()
        xyz.write()









# def make_sets_npoints(
#     points: ListOfAtoms, set_size: int, methods: List[str]
# ) -> int:
#     """Return the total number of points that are going to be used to initialize the training set. Multiple initialization methods
#     can be combined to give the total number of initial training points."""

#     npoints = 0
#     for method in methods:
#         for MakeSet in MAKE_SET_METHODS.values():
#             if method == MakeSet.name():
#                 npoints += MakeSet.get_npoints(set_size, points)
#     return npoints

# def make_set_with_method(
#     points: ListOfAtoms, method: MakeSetMethod
# ) -> Tuple[ListOfAtoms, ListOfAtoms]:
#     points_to_get = list(
#         set(method.get_points(points))
#     )  # Get points and remove duplicates
#     new_set = ListOfAtoms()
#     for i in sorted(points_to_get, reverse=True):
#         new_set += [points[i]]
#         del points[i]
#     return new_set, points