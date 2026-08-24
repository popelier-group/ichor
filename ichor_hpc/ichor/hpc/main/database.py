from pathlib import Path
from typing import List, Optional, Tuple

from ichor.core.atoms import ALF

from ichor.core.useful_functions import single_or_many_points_directories
from ichor.hpc.batch_system import JobID
from ichor.hpc.global_variables import SCRIPT_NAMES
from ichor.hpc.useful_functions.submit_free_flow_python_on_compute import (
    submit_free_flow_python_command_on_compute,
)

# formats from PointsDirectory
AVAILABLE_DATABASE_FORMATS = {
    "sqlite": "write_to_sqlite3_database",
    "json": "write_to_json_database",
}


def database_path(points_dir_path: Path, database_format: str = "sqlite") -> Path:
    """Returns the path that the database made from the given PointsDirectory
    (or parent to PointsDirectory-ies) is written to.

    The database is written next to the PointsDirectory rather than inside it. A
    PointsDirectory holds one directory per point, so a database written inside one is a
    single file among thousands of point directories with much the same name as it, which
    makes it awkward to find (and to pass on to the stages which take the database as
    their input).

    :param points_dir_path: Path to the PointsDirectory or parent to PointsDirectory-ies
        the database is made from.
    :param database_format: The format the database is written in, sqlite or json.
    :return: The path of the database, which is a file for sqlite and a directory for
        json.
    """

    # the name of the PointsDirectory without its .pointsdir/.pointsdirparent suffix,
    # in the directory the PointsDirectory itself sits in
    stem_path = points_dir_path.parent / points_dir_path.stem
    is_parent_directory_to_many_points_directories = single_or_many_points_directories(
        points_dir_path
    )

    # these names are the ones the write methods of PointsDirectory and
    # PointsDirectoryParent give the database when they are handed `stem_path`
    if database_format == "json":
        if is_parent_directory_to_many_points_directories:
            return stem_path.with_name(f"{stem_path.name}_json_parent")
        return stem_path.with_name(f"{stem_path.name}_json")

    if is_parent_directory_to_many_points_directories:
        return stem_path.with_name(f"{stem_path.name}_parent.sqlite")
    return stem_path.with_suffix(".sqlite")


def processed_csvs_directory(db_path: Path) -> Path:
    """Returns the directory that the processed csv files of a database are written to,
    which sits next to the database itself and is named after the system.

    :param db_path: Path to the database (a .sqlite file or a json database directory).
    :return: The path of the directory holding the per-atom csv files.
    """

    # find system name from the database name, stripping whichever suffix it carries
    system_name = db_path.name
    for suffix in (".pointsdir", ".pointsdirparent", ".sqlite"):
        system_name = system_name.removesuffix(suffix)

    return db_path.parent / f"0_{system_name}_processed_csvs"


def submit_make_database(
    points_dir_path: Path,
    database_format: str = "sqlite",
    ncores: int = 1,
):
    """Method for making a PointsDirectory or parent to PointsDirectory into a database.
    Infers if it is a PointsDirectory or PointsDirectoryParent based on the suffix of
    the directory

    :param points_dir_path: Path to PointsDirectory or parent to PointsDirectory-ies
    :param database_format: the format, currently sqlite and json are supported
    :param ncores: number of cores to use on compute node
    """

    is_parent_directory_to_many_points_directories = single_or_many_points_directories(
        points_dir_path
    )

    # the write methods add the suffix of the format to this themselves, so they are
    # given the name without one (see `database_path`, which says where that ends up)
    db_name = points_dir_path.parent / points_dir_path.stem

    # this is used to be able to call the respective methods from PointsDirectory
    # so that the same code below is used with the respective methods
    str_database_method = AVAILABLE_DATABASE_FORMATS[database_format]

    # if turning many PointsDirectories into db on compute node
    if is_parent_directory_to_many_points_directories:

        text_list = []
        # make the python command that will be written in the submit script
        # it will get executed as `python -c python_code_to_execute...`
        text_list.append("from ichor.core.files import PointsDirectoryParent")
        text_list.append("from pathlib import Path")
        # needs to be a list comprehension because for loops do not work with -c flag
        # need to write each pointdirectory to a separate json directory
        text_list.append(f"pd_parent = Path('{str(points_dir_path.absolute())}')")
        text_list.append(
            f"PointsDirectoryParent(pd_parent).{str_database_method}('{db_name}')"
        )

        return submit_free_flow_python_command_on_compute(
            text_list, SCRIPT_NAMES["pd_to_database"], ncores=ncores
        )

    # if only one PointsDirectory to db
    else:

        text_list = []
        # make the python command that will be written in the submit script
        # it will get executed as `python -c python_code_to_execute...`
        text_list.append("from ichor.core.files import PointsDirectory")
        text_list.append("from pathlib import Path")
        text_list.append(f"pd = PointsDirectory('{str(points_dir_path.absolute())}')")
        text_list.append(f"pd.{str_database_method}('{db_name}')")

        return submit_free_flow_python_command_on_compute(
            text_list, SCRIPT_NAMES["pd_to_database"], ncores=ncores
        )


def submit_make_csvs_from_database(
    db_path: Path,
    db_type: str,
    ncores: int,
    alf: List[ALF] = None,
    float_difference_iqa_wfn: float = 4.184,
    float_integration_error: float = 1e-3,
    rotate_multipole_moments: bool = True,
    calculate_feature_forces: bool = False,
    hold: Optional[JobID] = None,
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
    :param hold: An optional JobID to hold for. The csv job will not start until that
        other job has finished, which is how it is chained behind the job which makes the
        database it reads.
    """
    # path to save the processed csvs to, next to the database itself
    csvs_path = processed_csvs_directory(db_path)

    text_list = []
    # make the python command that will be written in the submit script
    # it will get executed as `python -c python_code_to_execute...`
    text_list.append(
        "from ichor.core.database import write_processed_data_for_atoms_parallel"
    )
    text_list.append("from pathlib import Path")
    text_list.append("from ichor.core.atoms import ALF")
    text_list.append(f"db_path = Path('{db_path.absolute()}')")

    # the ALF is read from the first geometry of the database. When it is not given, that
    # read is done by the job itself rather than here, as here is the login node at the
    # time the job is submitted, which is before the database exists at all if this job is
    # held on the one which makes it
    if alf:
        text_list.append(f"alf = {alf}")
    else:
        text_list.append(
            "from ichor.core.database import get_alf_from_first_db_geometry"
        )
        text_list.append(f"alf = get_alf_from_first_db_geometry(db_path, '{db_type}')")
    str_part1 = (
        f"write_processed_data_for_atoms_parallel(db_path, '{db_type}', alf, {ncores},"
    )
    str_part2 = f" max_diff_iqa_wfn={float_difference_iqa_wfn},"
    str_part3 = f" max_integration_error={float_integration_error},"
    str_part4 = f" calc_multipoles={rotate_multipole_moments}, calc_forces={calculate_feature_forces},"
    str_part5 = f" parent_directory='{csvs_path}')"

    text_list.append(str_part1 + str_part2 + str_part3 + str_part4 + str_part5)

    return submit_free_flow_python_command_on_compute(
        text_list=text_list,
        script_name=SCRIPT_NAMES["calculate_features"],
        ncores=ncores,
        hold=hold,
    )


def submit_make_database_and_csvs(
    points_dir_path: Path,
    database_format: str = "sqlite",
    ncores: int = 1,
    csv_ncores: int = 4,
    float_difference_iqa_wfn: float = 4.184,
    float_integration_error: float = 1e-3,
    rotate_multipole_moments: bool = True,
    calculate_feature_forces: bool = False,
) -> Tuple[Optional[JobID], Optional[JobID]]:
    """Submits the two jobs which turn a PointsDirectory into the csv files that model
    training reads: one which makes the database, and one which is held behind it and
    makes the csvs out of that database.

    The csv job is held on the database job by the batch system, so it does not start
    until the database has been written. Nothing about the database is read here, at
    submission time, as it does not exist yet: where it will be written is worked out from
    the PointsDirectory (see :func:`database_path`) and the ALF is read by the csv job
    itself once it starts.

    :param points_dir_path: Path to PointsDirectory or parent to PointsDirectory-ies.
    :param database_format: The format the database is written in, sqlite or json.
    :param ncores: Number of cores the database job asks for. It reads the points one at a
        time, so this is how it is given memory rather than a way of making it faster.
    :param csv_ncores: Number of cores the csv job asks for. That job is parallelised per
        atom, so the number of atoms in the system is the optimal choice.
    :param float_difference_iqa_wfn: Absolute tolerance for difference of energy between
        WFN and sum of IQA energies.
    :param float_integration_error: Absolute tolerance for integration error.
    :param rotate_multipole_moments: Whether or not to rotate multipole moments.
    :param calculate_feature_forces: Whether or not to calculate ALF forces.
    :return: (the JobID of the database job, the JobID of the csv job). The csv job is not
        submitted, and is None, if the database job was not.
    """

    database_job_id = submit_make_database(
        points_dir_path,
        database_format,
        ncores=ncores,
    )

    if not database_job_id:
        return database_job_id, None

    csvs_job_id = submit_make_csvs_from_database(
        database_path(points_dir_path, database_format),
        database_format,
        ncores=csv_ncores,
        alf=None,
        float_difference_iqa_wfn=float_difference_iqa_wfn,
        float_integration_error=float_integration_error,
        rotate_multipole_moments=rotate_multipole_moments,
        calculate_feature_forces=calculate_feature_forces,
        hold=database_job_id,
    )

    return database_job_id, csvs_job_id
