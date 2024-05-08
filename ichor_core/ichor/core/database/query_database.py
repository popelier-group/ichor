from pathlib import Path
from typing import List, Union

import pandas as pd
from ichor.core.atoms import ALF, Atom, Atoms
from ichor.core.calculators import (
    calculate_alf_atom_sequence,
    calculate_alf_features,
    get_atom_alf,
)
from ichor.core.common.constants import (
    spherical_dipole_labels,
    spherical_hexadecapole_labels,
    spherical_monopole_labels,
    spherical_octupole_labels,
    spherical_quadrupole_labels,
)
from ichor.core.common.str import get_characters
from ichor.core.database.json import get_json_db_info
from ichor.core.database.sql import get_sqlite_db_information
from ichor.core.models.gaussian_energy_derivative_wrt_features import (
    convert_to_feature_forces,
    form_b_matrix,
)
from ichor.core.multipoles import (
    rotate_dipole,
    rotate_hexadecapole,
    rotate_octupole,
    rotate_quadrupole,
)


# TODO: move this to somewhere  else
def rotate_multipole_moments(row_with_atom_info, C):

    local_spherical_multipoles = {
        spherical_monopole_labels[0]: row_with_atom_info["q00"].item()
    }

    local_dipole_moments = rotate_dipole(
        *(
            row_with_atom_info[dipole_label].item()
            for dipole_label in spherical_dipole_labels
        ),
        C,
    )
    for dipole_name, dipole_value in zip(spherical_dipole_labels, local_dipole_moments):
        local_spherical_multipoles[dipole_name] = dipole_value

    local_quadrupole_moments = rotate_quadrupole(
        *(
            row_with_atom_info[quadrupole_label].item()
            for quadrupole_label in spherical_quadrupole_labels
        ),
        C,
    )
    for quadrupole_name, quadrupole_value in zip(
        spherical_quadrupole_labels, local_quadrupole_moments
    ):
        local_spherical_multipoles[quadrupole_name] = quadrupole_value

    local_octupole_moments = rotate_octupole(
        *(
            row_with_atom_info[octupole_label].item()
            for octupole_label in spherical_octupole_labels
        ),
        C,
    )
    for octupole_name, octupole_value in zip(
        spherical_octupole_labels, local_octupole_moments
    ):
        local_spherical_multipoles[octupole_name] = octupole_value

    local_hexadecapole_moments = rotate_hexadecapole(
        *(
            row_with_atom_info[hexadecapole_label].item()
            for hexadecapole_label in spherical_hexadecapole_labels
        ),
        C,
    )
    for hexadecapole_name, hexadecapole_value in zip(
        spherical_hexadecapole_labels, local_hexadecapole_moments
    ):
        local_spherical_multipoles[hexadecapole_name] = hexadecapole_value

    return local_spherical_multipoles


def check_supported_db_types(db_type: str):
    """Checks the given database type, raises ValueError if it is not present."""

    _supported_databases = ["json", "sqlite"]

    if db_type not in _supported_databases:
        raise ValueError(
            f"Database type is not found in supported formats: {_supported_databases}."
        )


def get_database_info_from_db_type(db_path: Union[str, Path], db_type: str, echo=False):
    """Gets the required information from the database to make processed csvs.
    Works for sqlite or json

    :param db_path: path to database
    :param db_type: the type of database containing info, currently only "json" and "sqlite" are supported.
    :raises ValueError: If the value of db_type is not in supported databases.
    """

    check_supported_db_types(db_type)

    if db_type == "sqlite":
        point_ids, all_atom_names, full_df = get_sqlite_db_information(
            db_path, echo=echo
        )
    elif db_type == "json":
        point_ids, all_atom_names, full_df = get_json_db_info(db_path)

    return point_ids, all_atom_names, full_df


def get_alf_from_first_db_geometry(
    db_path: Union[str, Path],
    db_type: str,
    alf_calc_func=calculate_alf_atom_sequence,
    echo=False,
) -> List[ALF]:
    """
    Returns the atomic local frame for every atom from the first point.

    :param db_path: Path to SQLite3 database containing `Points`, `AtomNames`, and `Dataset` tables.
    :param db_type: The type of database, currently only sqlite and json supported
    :param alf_calc_func: The function to calculate ALF with on an Atoms instance
    :param echo: Whether to echo executed SQL queries, defaults to False
    :return: A list of ALF instances for every atom in the system.
    """

    check_supported_db_types(db_type)

    ids, _, full_df = get_database_info_from_db_type(db_path, db_type, echo=echo)

    first_point_id = ids[0]

    atoms = Atoms()

    one_point_df = full_df.loc[full_df["id"] == first_point_id]

    for row_id, row_data in one_point_df.iterrows():
        atom_type = get_characters(row_data.atom_name)
        atoms.append(Atom(atom_type, row_data.x, row_data.y, row_data.z))

    return atoms.alf_list(alf_calc_func)


# needed for parallel job, because it does not work with closed over functions (or lambdas)
# need to execute a globally defined a function to be mapped by ProcessPool
_func = None


def worker_init(func):
    global _func
    _func = func


def worker(x):
    return _func(x)


def write_processed_data_for_atoms_parallel(
    db_path: Union[str, Path],
    db_type: List[str],
    alf: List[ALF],
    ncores: int,
    max_diff_iqa_wfn: float = 4.184,
    max_integration_error: float = 0.001,
    atom_names: List[str] = None,
    write_index_col=False,
    echo=False,
    calc_multipoles: bool = True,
    calc_forces: bool = False,
    parent_directory: Path = Path("processed_csvs"),
):
    """
    Function uses the concurrent.futures.ProcessPoolExecutor class to parallelize the calculations
    on multiple cores, so that multiple atom calculations can be done in parallel.

    Writes a csv containing the features, wfn energy, -dE/df (note that these are forces wtr features),
    iqa energy, and rotated multipoles for every atom in the SQL database.
    Note that only points for which the absolute integration error for the atom of interest
    is below the threshold are added to the
    corresponding atomic datasets.

    :param db_path: Path to SQLite3 database containing `Points`, `AtomNames`, and `Dataset` tables.
        or a json database (a directory), potentially containing multiple directories
    :param db_type: The type of database that is given, currently only json or sqlite formats supported.
    :param alf: A list of ALF instances to be used when calculating features
        and calculating C matrices.
    :param ncores: The number of cores to use for the parallel calculations. Each core will calculate
        the data for an individual atom.
    :param max_diff_iqa_wfn: The maximum difference between the sum of iqa and wfn energy (in kJ mol-1). Any point
        that is above this threshold will be filtered out before doing integration errors.
    :param max_integration_error: Maximum integration error that a point needs to have for the atom
        of interest. Having a higher (absolute) integration error for the atom of interest means that
        this point will not be added in the dataset for the atom of interest. However, the same
        point can be added in the dataset for another atom, if the integration error is good, defaults to 0.001
    :param write_index_col: Whether to write the index col in the final .csv file, defaults to False
    :param echo: Whether to echo executed SQL statements, defaults to False
    :param atom_names: A list of atom names for which to write db. If left to None, csv files
        will be written for all atoms.
    :param calc_forces: Whether to calculate -dE/df, default False.
    """
    import concurrent.futures
    import multiprocessing

    CPU_COUNT = multiprocessing.cpu_count()

    if CPU_COUNT < ncores:
        raise ValueError(
            f"The number of available cores {CPU_COUNT} is less than the selected number of cores {ncores}."
        )

    point_ids, all_atom_names, full_df = get_database_info_from_db_type(
        db_path, db_type, echo=echo
    )

    # if no names given, make csvs for all atoms
    if not atom_names:
        atom_names = all_atom_names

    # needed for parallel lambda
    def func_for_parallel(atom_name):

        write_processed_one_atom_data_to_csv(
            full_df,
            point_ids,
            atom_name=atom_name,
            alf=alf,
            max_diff_iqa_wfn=max_diff_iqa_wfn,
            max_integration_error=max_integration_error,
            write_index_col=write_index_col,
            calc_multipoles=calc_multipoles,
            calc_forces=calc_forces,
            parent_directory=parent_directory,
        )

    # need to execute a globally defined a function, so this initializer and initialargs do that
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=ncores, initializer=worker_init, initargs=(func_for_parallel,)
    ) as executor:

        executor.map(worker, atom_names)


def write_processed_data_for_atoms(
    db_path: Union[str, Path],
    db_type: str,
    alf: List[ALF],
    max_integration_error: float = 0.001,
    write_index_col=False,
    echo=False,
    atom_names: List = None,
    calc_multipoles: bool = True,
    calc_forces: bool = False,
):
    """Writes a csv containing the features, wfn energy, -dE/df (note that these are forces wtr features),
        iqa energy, and rotated multipoles for every atom in the SQL database.
        Note that only points for which the absolute integration error for the atom of interest
        is below the threshold are added to the
        corresponding atomic datasets.

    :param db_path: Path to SQLite3 database containing `Points`, `AtomNames`, and `Dataset` tables.
    :param db_type: type of database, sqlite or json
    :param alf: A list of ALF instances to be used when calculating features
        and calculating C matrices.
    :param max_integration_error: Maximum integration error that a point needs to have for the atom
        of interest. Having a higher (absolute) integration error for the atom of interest means that
        this point will not be added in the dataset for the atom of interest. However, the same
        point can be added in the dataset for another atom, if the integration error is good, defaults to 0.001
    :param write_index_col: Whether to write the index col in the final .csv file, defaults to False
    :param echo: Whether to echo executed SQL statements, defaults to False
    :param atom_names: A list of atom names for which to write db. If left to None, csv files
        will be written for all atoms.
    :param properties: Which properties to write out to csv files.
    """

    point_ids, all_atom_names, full_df = get_database_info_from_db_type(
        db_path, db_type, echo=echo
    )

    if not atom_names:
        atom_names = all_atom_names

    for atom_name in atom_names:

        write_processed_one_atom_data_to_csv(
            full_df,
            point_ids,
            atom_name=atom_name,
            alf=alf,
            max_integration_error=max_integration_error,
            write_index_col=write_index_col,
            calc_multipoles=calc_multipoles,
            calc_forces=calc_forces,
        )


# TODO: add logic that calculates rotated multipoles only (encomp=0) and does integration
# error only for rotated multipoles
def write_processed_one_atom_data_to_csv(
    full_df: pd.DataFrame,
    point_ids: List[int],
    atom_name: str,
    alf: List[ALF],
    max_diff_iqa_wfn: float = 4.184,  # this is 1 kcal mol-1 because some consider that "below chemical accuracy"
    max_integration_error: float = 0.001,  # 1e-3 is a decent enough value, can use 1e-4 instead as well
    write_index_col=False,
    calc_multipoles: bool = True,
    calc_forces: bool = False,
    parent_directory: Path = Path("processed_csvs"),
):
    """Writes features, iqa energy, as well as rotated multipole moments (given an ALF) to a csv file
    for all points (as long as integration error for the atom of interest is below a threshold integration error).

    :param full_df: DataFrame object extracted from SQLite database. This object contains information for
        all points (and all atoms in every point)
    :param point_ids: A list of integers representing the `id` column of the points table of the SQLite database.
    :param atom_name: The atom for which features, local multipole moments,
        as well as local forces are going to be calculated for every point in the dataset
    :param alf: A list of ALF instance to be used when calculating features
        and calculating C matrices
    :param max_diff_iqa_wfn: Maximum difference between sum of IQA and wfn energy (in kJ mol-1).
        If point is above threshold, it will get filtered before doing integration error.
    :param max_integration_error: Maximum integration error that a point needs to have for the atom
        of interest. Having a higher (absolute) integration error for the atom of interest means that
        this point will not be added in the dataset for the atom of interest. However, the same
        point can be added in the dataset for another atom, if the integration error is good, defaults to 0.001
    :param calc_forces: Whether to calculate -dE/df forces (which takes a long time currently), default False.
    """

    # make directory where csvs are going to be stored
    parent_directory.mkdir(exist_ok=True)

    # final dictionary that is going to be converted to pd.DataFrame and written to csv
    total_dict = {}

    # loop over points
    for point_id in point_ids:

        # find geometry which matches the id
        one_point_df = full_df.loc[full_df["id"] == point_id]

        # need to check that iqa is populated for all atoms before summing
        if not (one_point_df["iqa"].isnull().all()):
            sum_iqa_energies = one_point_df["iqa"].sum()
            # the wfn energy will be the same for all atoms, since they come from same geometry
            # so just grab first value
            abs_diff_wfn_iqa_kj_mol = (
                abs(one_point_df["wfn_energy"].values[0] - sum_iqa_energies) * 2625.5
            )
            # do not add point to the processed csv if difference is too large
            if abs_diff_wfn_iqa_kj_mol >= max_diff_iqa_wfn:
                continue

        # check that integration error is below threshold, otherwise do not calculate features
        # for the atom and do not add this point to training set for this atom.
        # if other atoms have good integration errors, the same point can be used in their training sets.
        row_with_atom_info = one_point_df.loc[one_point_df["atom_name"] == atom_name]

        if calc_forces:
            if not one_point_df["force_x"].isnull().values.any():
                global_forces_array = one_point_df[
                    ["force_x", "force_y", "force_z"]
                ].to_numpy()
            else:
                global_forces_array = None
        else:
            global_forces_array = None

        # If the atomic information (.int file) was missing, then this
        # iqa energy will be None, so it will not get executed
        if row_with_atom_info["iqa"].item():

            # if the absolute of the integration error is less than threshold, then calculate features
            if (
                abs(row_with_atom_info["integration_error"].item())
                < max_integration_error
            ):

                # create atoms instance which will be used to calculate features
                atoms = Atoms()
                for row_id, row_data in one_point_df.iterrows():
                    # atoms accepts atom type (but database contains the atom index as well)
                    atom_type = get_characters(row_data.atom_name)
                    atoms.append(Atom(atom_type, row_data.x, row_data.y, row_data.z))

                natoms = len(atoms)
                in_alf_atom_indices = get_atom_alf(atoms[atom_name], alf)
                not_in_alf_indices = [
                    i for i in range(natoms) if i not in in_alf_atom_indices
                ]

                x_axis_name = atoms[in_alf_atom_indices[1]].name

                # if there are only 2 atoms, this will be None
                check_for_xy_plane_atom = in_alf_atom_indices[2]

                # if not none, then do xy-plane and potentially others
                if check_for_xy_plane_atom is not None:

                    xy_plane_atom_name = atoms[in_alf_atom_indices[2]].name
                    # the xy plane atom moves in the xy plane, so it itself determines what the valence angle is
                    # the x-axis atom always stays on the x-axis
                    val_angle_name = xy_plane_atom_name

                    atom_ordering_in_features = [
                        x_axis_name,
                        xy_plane_atom_name,
                        val_angle_name,
                    ] + [atoms[i].name for i in not_in_alf_indices for _ in range(3)]

                # if it is none, then we only have x-axis feature
                else:
                    atom_ordering_in_features = [x_axis_name]

                C = atoms[atom_name].C(alf)
                central_atom_index = atoms[atom_name].i  # 0-indexed
                # calculate features for the atom of interest
                one_atom_features = atoms[atom_name].features(
                    calculate_alf_features, alf
                )
                n_features = len(one_atom_features)

                if global_forces_array is not None:
                    b_matrix = form_b_matrix(atoms, alf, central_atom_index)
                    negative_dE_df = convert_to_feature_forces(
                        global_forces_array, b_matrix, alf, central_atom_index
                    )
                else:
                    negative_dE_df = [None] * n_features

                # make dictionary of rotated multipoles
                if calc_multipoles:
                    local_spherical_multipoles = rotate_multipole_moments(
                        row_with_atom_info, C
                    )

                # add the point_id and name of point to dictionary
                point_id_str = str(point_id)
                total_dict[point_id_str] = {
                    "point_id": point_id,
                    "point_name": row_with_atom_info["name"].item(),
                }
                # add features to dictionary
                total_dict[point_id_str].update(
                    {
                        f"f{i}_{a}": one_atom_feature
                        for a, i, one_atom_feature in zip(
                            atom_ordering_in_features,
                            range(1, n_features + 1),
                            one_atom_features,
                        )
                    }
                )
                # add wfn energy to dictionary
                total_dict[point_id_str].update(
                    {"wfn_energy": row_with_atom_info["wfn_energy"].item()}
                )

                # add feature forces to dictionary (these are negative of gradient)
                if calc_forces:
                    # add -dE/df (forces wrt features) to dict
                    total_dict[point_id_str].update(
                        {
                            f"-dE/df{i}": neg_dE_df
                            for i, neg_dE_df in zip(
                                range(1, n_features + 1), negative_dE_df
                            )
                        }
                    )

                # add iqa to dictionary
                total_dict[point_id_str].update(
                    {"iqa": row_with_atom_info["iqa"].item()}
                )

                # add integration_error to dictionary
                total_dict[point_id_str].update(
                    {
                        "integration_error": row_with_atom_info[
                            "integration_error"
                        ].item()
                    }
                )

                if calc_multipoles:
                    # add all the rotated multipole moments
                    total_dict[point_id_str].update(local_spherical_multipoles)

        # if no iqa information found
        else:

            # create atoms instance which will be used to calculate features
            atoms = Atoms()
            for row_id, row_data in one_point_df.iterrows():
                # atoms accepts atom type (but database contains the atom index as well)
                atom_type = get_characters(row_data.atom_name)
                atoms.append(Atom(atom_type, row_data.x, row_data.y, row_data.z))

            natoms = len(atoms)
            in_alf_atom_indices = get_atom_alf(atoms[atom_name], alf)
            not_in_alf_indices = [
                i for i in range(natoms) if i not in in_alf_atom_indices
            ]

            x_axis_name = atoms[in_alf_atom_indices[1]].name

            # if there are only 2 atoms, this will be None
            check_for_xy_plane_atom = in_alf_atom_indices[2]

            # if not none, then do xy-plane and potentially others
            if check_for_xy_plane_atom is not None:

                xy_plane_atom_name = atoms[in_alf_atom_indices[2]].name
                # the xy plane atom moves in the xy plane, so it itself determines what the valence angle is
                # the x-axis atom always stays on the x-axis
                val_angle_name = xy_plane_atom_name

                atom_ordering_in_features = [
                    x_axis_name,
                    xy_plane_atom_name,
                    val_angle_name,
                ] + [atoms[i].name for i in not_in_alf_indices for _ in range(3)]

            # if it is none, then we only have x-axis feature
            else:
                atom_ordering_in_features = [x_axis_name]

            C = atoms[atom_name].C(alf)
            central_atom_index = atoms[atom_name].i  # 0-indexed
            # calculate features for the atom of interest
            one_atom_features = atoms[atom_name].features(calculate_alf_features, alf)
            n_features = len(one_atom_features)

            if global_forces_array is not None:
                b_matrix = form_b_matrix(atoms, alf, central_atom_index)
                negative_dE_df = convert_to_feature_forces(
                    global_forces_array, b_matrix, alf, central_atom_index
                )
            else:
                negative_dE_df = [None] * n_features
            # add the point_id and name of point to dictionary
            point_id_str = str(point_id)
            total_dict[point_id_str] = {
                "point_id": point_id,
                "point_name": row_with_atom_info["name"].item(),
            }
            # add features to dictionary
            total_dict[point_id_str].update(
                {
                    f"f{i}_{a}": one_atom_feature
                    for a, i, one_atom_feature in zip(
                        atom_ordering_in_features,
                        range(1, n_features + 1),
                        one_atom_features,
                    )
                }
            )
            # add wfn energy to dictionary
            total_dict[point_id_str].update(
                {"wfn_energy": row_with_atom_info["wfn_energy"].item()}
            )

            if calc_forces:
                # add -dE/df (forces wrt features) to dict
                total_dict[point_id_str].update(
                    {
                        f"-dE/df{i}": neg_dE_df
                        for i, neg_dE_df in zip(
                            range(1, n_features + 1), negative_dE_df
                        )
                    }
                )

    # add 1 because model files start with atom index 1
    alf_for_current_atom = [i + 1 for i in alf[central_atom_index]]
    alf_str = "alf_" + "_".join(list(map(str, alf_for_current_atom)))

    # write the total dict containing information for all points to a DataFrame and save
    total_df = pd.DataFrame.from_dict(total_dict, orient="index")
    total_df.to_csv(
        parent_directory / f"{atom_name}_processed_data_{alf_str}.csv",
        index=write_index_col,
    )
