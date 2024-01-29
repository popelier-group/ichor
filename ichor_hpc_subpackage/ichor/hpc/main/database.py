from pathlib import Path
from typing import List

from ichor.cli.useful_functions import single_or_many_points_directories

from ichor.core.atoms import ALF
from ichor.core.database import get_alf_from_first_db_geometry
from ichor.core.files import PointsDirectory
from ichor.hpc.global_variables import SCRIPT_NAMES
from ichor.hpc.useful_functions.submit_free_flow_python_on_compute import (
    submit_free_flow_python_command_on_compute,
)

# formats from PointsDirectory
AVAILABLE_DATABASE_FORMATS = {
    "sqlite": "write_to_sqlite3_database",
    "json": "write_json_database",
}


def submit_make_database(
    points_dir_path: Path,
    database_format: str = "sqlite",
    submit_on_compute: bool = True,
    ncores=1,
):
    """Method for making a PointsDirectory or parent to PointsDirectory into a database.
    Infers if it is a PointsDirectory or PointsDirectoryParent based on the suffix of
    the directory

    :param points_dir_path: Path to PointsDirectory or parent to PointsDirectory-ies
    :param database_format: the format, which will get added to the name of the file
        Currently, only the sqlite format is supported
    :param submit_on_compute: Whether or not to submit to compute node, defaults to True
    :param ncores: number of cores to use on compute node
    """

    if database_format not in AVAILABLE_DATABASE_FORMATS.keys():
        print(
            f"The given database format, {database_format} is not in the available formats:",
            ",".join(AVAILABLE_DATABASE_FORMATS.keys()),
        )

    is_parent_directory_to_many_points_directories = single_or_many_points_directories(
        points_dir_path
    )

    path_stem = points_dir_path.stem
    db_name = path_stem

    # this is used to be able to call the respective methods from PointsDirectory
    # so that the same code below is used with the respective methods
    str_database_method = AVAILABLE_DATABASE_FORMATS[database_format]

    # if running on login node, discouraged because takes a long time
    if not submit_on_compute:

        # if running on a directory containing many PointsDirectories
        if is_parent_directory_to_many_points_directories:

            for d in points_dir_path.iterdir():

                pd = PointsDirectory(d)
                # write all data to a single database by passing in the same name for every PointsDirectory
                # get the method and pass in the database path name
                getattr(pd, str_database_method)(db_name)

        else:
            pd = PointsDirectory(points_dir_path)
            getattr(pd, str_database_method)(db_name)

    # if running on compute node
    else:

        # if turning many PointsDirectories into db on compute node
        if is_parent_directory_to_many_points_directories:

            text_list = []
            # make the python command that will be written in the submit script
            # it will get executed as `python -c python_code_to_execute...`
            text_list.append("from ichor.core.files import PointsDirectory")
            text_list.append("from pathlib import Path")
            # make the parent directory path in a Path object
            text_list.append(f"parent_dir = Path('{points_dir_path.absolute()}')")

            # make a list comprehension that writes each PointsDirectory in the parent dir
            # into the same SQLite database
            # needs to be a list comprehension because for loops do not work with -c flag
            str_part1 = f"[PointsDirectory(d).{str_database_method}('{db_name}', print_missing_data=True)"
            str_part2 = " for d in parent_dir.iterdir()]"

            total_str = str_part1 + str_part2

            text_list.append(total_str)

            return submit_free_flow_python_command_on_compute(
                text_list, SCRIPT_NAMES["pd_to_database"], ncores=ncores
            )

        # if only one PointsDirectory to db
        else:

            text_list = []
            # make the python command that will be written in the submit script
            # it will get executed as `python -c python_code_to_execute...`
            text_list.append("from ichor.core.files import PointsDirectory")
            text_list.append(f"pd = PointsDirectory('{points_dir_path.absolute()}')")
            text_list.append(
                f"pd.{str_database_method}('{db_name}', print_missing_data=True)"
            )

            return submit_free_flow_python_command_on_compute(
                text_list, SCRIPT_NAMES["pd_to_database"], ncores=ncores
            )


def submit_make_csvs_from_database(
    db_path: Path,
    db_type: str,
    ncores: int,
    alf: List[ALF] = None,
    submit_on_compute=True,
    float_difference_iqa_wfn: float = 4.184,
    float_integration_error: float = 1e-3,
    rotate_multipole_moments: bool = True,
    calculate_feature_forces: bool = False,
):
    """Submits making of csv files from a databse to compute node.
    Note that the csv making code is parallelized per atom, meaning that
    each atomic csv is made using 1 core. Using the same number of cores
    as the number of atoms in the system is the optimal choice.

    :param db_path: pathlib.Path object that holds path to database
    :param db_type: The type of database, sqlite or json
    :param ncores: Number of cores to run job with
    :param float_difference_iqa_wfn: Absolute tolerance for difference of energy
        between WFN and sum of IQA energies.
    :param submit_on_compute: Whether to submit on compute or now
    :param float_integration_error: Absolute tolerance for integration error.
    :param alf: A list of ALF for the whole system. If not given,
        it will be calculated automatically.
    :param rotate_multipole_moments: Whether or not to rotate multipole
        moments, defaults to True
    :param calculate_feature_forces: Whether or not to calculate ALF forces, defaults to False
    """

    # if no alf is given, then automatically calculate it
    if not alf:
        alf = get_alf_from_first_db_geometry(db_path, db_type)

    if submit_on_compute:

        text_list = []
        # make the python command that will be written in the submit script
        # it will get executed as `python -c python_code_to_execute...`
        text_list.append(
            "from ichor.core.database import write_processed_data_for_atoms_parallel"
        )
        text_list.append("from pathlib import Path")
        text_list.append("from ichor.core.atoms import ALF")
        text_list.append(f"db_path = Path('{db_path.absolute()}')")
        text_list.append(f"alf = {alf}")
        str_part1 = f"write_processed_data_for_atoms_parallel(db_path, {db_type}, alf, {ncores},"
        str_part2 = f" max_diff_iqa_wfn={float_difference_iqa_wfn},"
        str_part3 = f" max_integration_error={float_integration_error},"
        str_part4 = f" calc_multipoles={rotate_multipole_moments}, calc_forces={calculate_feature_forces})"
        text_list.append(str_part1 + str_part2 + str_part3 + str_part4)

        return submit_free_flow_python_command_on_compute(
            text_list=text_list,
            script_name=SCRIPT_NAMES["calculate_features"],
            ncores=ncores,
        )

    else:

        from ichor.core.database import write_processed_data_for_atoms_parallel

        write_processed_data_for_atoms_parallel(
            db_path,
            db_type,
            alf,
            ncores,
            max_diff_iqa_wfn=float_difference_iqa_wfn,
            max_integration_error=float_integration_error,
            calc_multipoles=rotate_multipole_moments,
            calc_forces=calculate_feature_forces,
        )
