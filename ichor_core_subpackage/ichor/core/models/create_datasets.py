import random
from pathlib import Path
from typing import List, Tuple, Union

import pandas as pd

# these work with csv files written out by ichor


def get_atom_name_and_alf_from_csv(csv_path: Path) -> Tuple[str, List[str]]:
    """Helper function to get atom name and alf (as list of str)

    :param csv_path: The csv file path
    :return: A tuple containing the atom name and alf
    """

    # files are in the form H6_processed_data_alf_5_3_4.csv
    atom_name = csv_path.stem.split("_")[0]
    alf_list = csv_path.stem.split("_")[-3:]

    return atom_name, alf_list


def write_csvs_intersection(
    input_dir: Union[str, Path] = "processed_csvs",
    output_dir: Union[str, Path] = "processed_csvs_intersection",
):
    """Not all processed atom csvs might contain the same points. This is because
    one atom might in a point might be filtered because of integration error but another
    one might not. This function is used to write out datasets that enforce that all atoms
    in a point are present in the written out csvs. The function finds the
    intersection of all point names across the csvs and then only writes out the
    rows from each csv that are in the intersection.

    :param input_dir: The path to the directory containing processed csvs files, defaults to "processed_csvs"
    :param output_dir: The path to the directory containing output csvs, defaults to "processed_csvs_all_atoms"
    """

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # read in all csvs
    all_dfs = [
        pd.read_csv(csv_file, header=0, index_col=0) for csv_file in input_dir.iterdir()
    ]

    # get a list of sets
    # the point names in the dfs should already be unique
    unique_points_in_all_csvs_list = [set(df["point_name"]) for df in all_dfs]
    # get intersection of the list of sets
    intersection_of_point_names_in_all_csvs = set.intersection(
        *unique_points_in_all_csvs_list
    )
    print(
        "Number of intersection points:", len(intersection_of_point_names_in_all_csvs)
    )

    # read the files again because we need to get some info from them
    for csv_file in input_dir.iterdir():

        atom_name, alf_list = get_atom_name_and_alf_from_csv(csv_file)

        df = pd.read_csv(csv_file, header=0, index_col=0)

        # get rows where we know all atoms of a point are present in the csvs
        df = df[df["point_name"].isin(intersection_of_point_names_in_all_csvs)]

        # write output file
        output_file_name = f"{atom_name}_processed_data_all_atoms_alf_{alf_list[0]}_{alf_list[1]}_{alf_list[2]}.csv"
        output_path = output_dir / output_file_name
        df.to_csv(output_path, index=True, header=True)


def write_multiple_train_sets_and_one_test_set(
    ntrain_initial: int,
    ntrain_increment: int,
    nincrements: int,
    ntest: int,
    processed_csvs_dir: Union[str, Path] = "processed_csvs",
    set_path=Path("sets"),
):
    """
    .. warning::

        The function assumes that csvs contain ALL the same points in them.

    .. note::
        If there are 0 increments, then it will only make one training set and one test set
        containing random points (points in the training set are NOT in the test set).

    Function used to generate (multiple)training sets and one test set. The training sets contain
    an increasing number of training points, where bigger training sets contain the smaller training sets
    in them already. The test set contains points that are outside of the training sets.

    :param ntrain_initial: smallest possible training set size
    :param ntrain_increment: how much to increase the training set size by
    :param nincrements: how many times to increase the training set size
    :param ntest: number of test set points
    :param processed_csvs_dir: Location of processed csvs containing sample set, defaults to "processed_csvs"
    :param set_path: The output directory which will contain the train/test sets, defaults to Path("sets")
    :raises ValueError: if the training+test set size is above the sample set size
    """

    processed_csvs_dir = Path(processed_csvs_dir)
    set_path = Path(set_path)
    set_path.mkdir(exist_ok=True)

    # check that the highest number of training points plus the test points is not above the npoints
    npoints = len(
        pd.read_csv(next(processed_csvs_dir.iterdir()), header=0, index_col=0)
    )

    if (ntrain_initial + nincrements * ntrain_increment) + ntest > npoints:
        raise ValueError(
            "The number of points in less than the requested test+train set sizes."
        )

    # get random indices for training set between 0 and npoints
    # these will be the same for all datasets
    test_point_indices = random.sample(range(0, npoints), ntest)
    all_possible_training_set_indices = set(
        [i for i in range(0, npoints) if i not in test_point_indices]
    )

    # function to make training sets of different sizes
    def make_dataset(csv_path, atom_name, alf, point_indices, ty):

        if ty == "test":
            inner_dir_path = Path(set_path / f"test_{len(point_indices)}")
            inner_csv_path = (
                inner_dir_path
                / f"{atom_name}_test_data_alf_{alf[0]}_{alf[1]}_{alf[2]}.csv"
            )
        elif ty == "train":
            inner_dir_path = Path(set_path / f"train_{len(point_indices)}")
            inner_csv_path = (
                inner_dir_path
                / f"{atom_name}_training_data_alf_{alf[0]}_{alf[1]}_{alf[2]}.csv"
            )
        else:
            raise ValueError("ty can either be 'test' or 'train'.")

        full_df = pd.read_csv(csv_path, index_col=0, header=0)
        df_to_write = full_df.iloc[point_indices]

        inner_dir_path.mkdir(exist_ok=True)
        df_to_write.to_csv(inner_csv_path)

    # make test sets
    for csv_file in Path(processed_csvs_dir).iterdir():

        atom_name, alf = get_atom_name_and_alf_from_csv(csv_file)

        make_dataset(csv_file, atom_name, alf, test_point_indices, "test")

    # get initial training set size
    training_indices = random.sample(all_possible_training_set_indices, ntrain_initial)

    # loop over number of increments
    # first loop will not add any points
    # add one so that last increment is included
    for incr in range(nincrements + 1):

        # get random indices to add to training set
        random_points_indices_to_add = random.sample(
            all_possible_training_set_indices, ntrain_increment
        )
        # don't add anything on first loop
        if not incr == 0:
            training_indices += random_points_indices_to_add
            # remove the chosen random indices, so they cannot be chosen again
            all_possible_training_set_indices = set(
                all_possible_training_set_indices
            ) - set(random_points_indices_to_add)

        for csv_file in Path(processed_csvs_dir).iterdir():

            atom_name, alf = get_atom_name_and_alf_from_csv(csv_file)

            make_dataset(csv_file, atom_name, alf, training_indices, "train")


def write_random_train_test_sets(
    ntrain: int,
    ntest: int,
    processed_csvs_dir: Union[str, Path] = "processed_csvs",
    set_path=Path("sets"),
):
    """Writes out a random training and test set

    :param ntrain: Number of training points
    :param ntest: Number of test points
    :param processed_csvs_dir: Directory with sample set csv files, defaults to "processed_csvs"
    :param set_path: Directory where train/test csvs are going to be written, defaults to Path("sets")
    """

    # just call the same function but do not increment training set size
    write_multiple_train_sets_and_one_test_set(
        ntrain, 0, 0, ntest, processed_csvs_dir, set_path
    )
