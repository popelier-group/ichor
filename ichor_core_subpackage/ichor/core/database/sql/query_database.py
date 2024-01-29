from pathlib import Path
from sqlite3 import Connection as SQLite3Connection
from typing import List, Tuple, Union

import pandas as pd
import sqlalchemy
from ichor.core.atoms import Atom, Atoms
from ichor.core.common.str import get_characters
from ichor.core.database.sql.add_to_database import AtomNames, Dataset, Points
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


def create_sqlite_db_engine(
    db_path: Union[str, Path], echo=False
) -> sqlalchemy.engine.Engine:
    """Creates an engine to a SQLite3 database and returns the Engine object.

    :param db_path: Path to SQLite3 database
    :param echo: Whether to echo SQL queries, defaults to False
    :return: An egnine object for the SQL database
    :rtype: sqlalchemy.engine.Engine
    """
    database_path = str(Path(db_path).absolute())
    # create database engine and start session
    engine = create_engine(
        f"sqlite+pysqlite:///{database_path}", echo=echo, future=True
    )

    return engine


def create_sqlite_db_connection(
    db_path: Union[str, Path], echo=False
) -> sqlalchemy.engine.Connection:
    """Creates a connection to a SQLite3 database and returns a connection object to be used
        when executing SQL statements with pandas.

    :param db_path: Path to SQLite3 database
    :param echo: Whether to echo SQL queries, defaults to False
    :return: A connection object to the SQL database
    :rtype: sqlalchemy.engine.Connection
    """

    database_path = str(Path(db_path).absolute())

    # create database engine and start session
    engine = create_engine(
        f"sqlite+pysqlite:///{database_path}", echo=echo, future=True
    )
    conn = engine.connect()

    return conn


def raw_one_atom_data_to_df_sqlite(
    db_path: Union[str, Path],
    atom_name: str,
    integration_error: float = 0.001,
    echo=False,
    drop_irrelevant_cols=True,
) -> pd.DataFrame:
    """Returns a pandas DataFrame object containing data for one atom.

    :param db_path: Path or str to SQLite3 database
    :param atom_name: string of atom name (e.g. `C1`)
    :param integration_error: Integration error for AIMAll. Any point with a higher
        absolute integration error will not be selected, defaults to 0.001
    :param echo: Whether to echo the executed SQL queries, defaults to False
    :param drop_irrelevant_cols: Whether to drop irrelevant columns (id columns that do not contain data)
        from the DataFrame, defaults to True
    :return: pd.DataFrame object containing the information for the DataFrame
    """

    conn = create_sqlite_db_connection(db_path, echo=echo)

    stmt = (
        select(Points, Dataset, AtomNames)
        .join(Points)
        .join(AtomNames)
        .where(func.abs(Dataset.integration_error) < integration_error)
        .where(AtomNames.name == atom_name)
    )

    df = pd.read_sql(stmt, conn)

    # need to rename because the atom table has column "name"
    # and points table also has column "name"
    df = df.rename(columns={"name_1": "atom_name"})

    # drop columns which contain IDs and other things from SQLAlchemy query
    if drop_irrelevant_cols:
        df = df.drop(
            ["id", "id_1", "point_id", "atom_id", "atom_name", "id_2"], axis="columns"
        )

    return df


def write_raw_one_atom_data_to_csv_sqlite(
    db_path: Union[str, Path],
    atom_name: str,
    integration_error: float = 0.001,
    echo=False,
    drop_irrelevant_cols=True,
):
    """Saves the raw data for one atom as stored in the SQLite3 database to a csv file.

    :param db_path: Path or str to SQLite3 database
    :param atom_name: string of atom name (e.g. `C1`)
    :param integration_error: Integration error for AIMAll. Any point with a higher
        absolute integration error will not be selected, defaults to 0.001
    :param echo: Whether to echo the executed SQL queries, defaults to False
    :param drop_irrelevant_cols: Whether to drop irrelevant columns (id columns that do not contain data)
        from the DataFrame, defaults to True
    """

    df = raw_one_atom_data_to_df_sqlite(
        db_path, atom_name, integration_error, echo, drop_irrelevant_cols
    )
    df.to_csv(f"raw_db_data_{atom_name}.csv")


def get_list_of_point_ids_from_sqlite_db(
    db_path: Union[str, Path], echo=False
) -> List[str]:
    """Returns a list of all the point names in the database

    :param db_path: Path or string to database
    :param echo: Whether to echo SQL queries, defaults to False
    :return: List of strings of the point names
    """
    conn = create_sqlite_db_connection(db_path, echo=echo)

    stmt = select(Points)
    df = pd.read_sql(stmt, conn)

    return list(df["id"])


def get_list_of_atom_names_from_sqlite_db(
    db_path: Union[str, Path], echo=False
) -> List[str]:
    """Returns a list of all the point names in the database

    :param db_path: Path or string to database
    :param echo: Whether to echo SQL queries, defaults to False
    :return: List of strings of the atom names
    """
    conn = create_sqlite_db_connection(db_path, echo=echo)

    stmt = select(AtomNames)
    df = pd.read_sql(stmt, conn)

    return list(df["name"])


def get_full_dataframe_for_all_atoms(
    db_path: Union[str, Path], echo=False, change_cols=True
) -> pd.DataFrame:
    """Returns a dataframe containing all the data for all atoms

    :param db_path: Path or str to database
    :param echo: Whether to echo SQL statements, defaults to False
    :param change_cols: Removes some unnecessary columns and also renames some columns
        to be more clear.
    :return: A pandas dataframe containing information for all atoms
    """

    conn = create_sqlite_db_connection(db_path=db_path, echo=echo)

    stmt = (
        select(Points, Dataset, AtomNames)
        .join(Dataset, Dataset.point_id == Points.id)
        .join(AtomNames, Dataset.atom_id == AtomNames.id)
    )
    # do not check integration error here, just always get full df with all atoms
    # .where(func.abs(Dataset.integration_error) < integration_error)
    # )

    full_df = pd.read_sql(stmt, conn)

    # need to rename because the atom table has column "name"
    # and points table also has column "name"
    full_df = full_df.rename(columns={"name_1": "atom_name"})

    # drop columns which contain IDs and other things from SQLAlchemy query
    if change_cols:
        full_df = full_df.drop(["id_1", "point_id", "atom_id", "id_2"], axis="columns")

    return full_df


def get_sqlite_db_information(
    db_path: Union[str, Path], echo=False
) -> Tuple[List[str], List[str], pd.DataFrame]:
    """Gets relevant information from database needed to post process data and generate datasets
    for machine learning

    :param db_path: Path to SQLite3 database containing `Points`, `AtomNames`, and `Dataset` tables.
    :param echo: Whether to echo executed SQL statements, defaults to False
    :return: Tuple of: List of point ids (integers) contained in the db,
                    List of atom names (str) contained in db,
                    a pd.DataFrame object containing all relevant data needed to construct the datasets.
    :rtype: Tuple[List[str], List[str], pd.DataFrame]
    """

    # get point ids to loop over
    point_ids = get_list_of_point_ids_from_sqlite_db(db_path=db_path, echo=echo)
    # get atom names to loop over
    atom_names = get_list_of_atom_names_from_sqlite_db(db_path, echo=echo)
    # full dataframe contains all atoms/points below some integration error
    full_df = get_full_dataframe_for_all_atoms(db_path=db_path, echo=echo)

    return point_ids, atom_names, full_df


def get_atoms_from_sqlite_point_id(full_df, point_id: int) -> "Atoms":
    """Returns an Atoms instance containing geometry for a point id.

    :param full_df: see get_df_information function
    :param point_id: The id of the point for which to get the geometry
    """

    # find geometry which matches the id
    one_point_df = full_df.loc[full_df["id"] == point_id]

    # create atoms instance which will be used to calculate features
    atoms = Atoms()
    for row_id, row_data in one_point_df.iterrows():
        # atoms accepts atom type (but database contains the atom index as well)
        atom_type = get_characters(row_data.atom_name)
        atoms.append(Atom(atom_type, row_data.x, row_data.y, row_data.z))

    return atoms


def delete_sqlite_points_by_id(engine, point_ids: List[int]):

    # need to enable this for SQLite3 database in order to delete correctly, see
    # https://stackoverflow.com/a/62327279
    @event.listens_for(Engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, SQLite3Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()

    session = Session(engine, future=True)
    session.query(Points).filter(Points.id.in_(point_ids)).delete()
    session.commit()


def trajectory_from_sqlite_database(
    point_ids, full_df, trajectory_name: str = "trajectory_from_database.xyz"
):
    """Writes our trajectory from geometries in database."""

    from ichor.core.files import Trajectory

    trajectory_inst = Trajectory(trajectory_name)

    for point_id in point_ids:
        atoms = get_atoms_from_sqlite_point_id(full_df, point_id)
        trajectory_inst.append(atoms)

    return trajectory_inst


def csv_file_with_specific_properties(
    point_ids, full_df, all_atom_names, properties: List[str]
):
    """Writes out csv file for each atom containing the given properties"""

    for atom_name in all_atom_names:
        with open(f"{atom_name}_properties.csv", "w") as f:
            f.write(",".join(properties) + "\n")
            for point_id in point_ids:
                # find geometry which matches the id
                one_point_df = full_df.loc[full_df["id"] == point_id]
                # check that integration error is below threshold, otherwise do not calculate features
                # for the atom and do not add this point to training set for this atom.
                # if other atoms have good integration errors, the same point can be used in their training sets.
                row_with_atom_info = one_point_df.loc[
                    one_point_df["atom_name"] == atom_name
                ]
                results = [str(row_with_atom_info[p]) for p in properties]
                f.write(",".join(results) + "\n")
