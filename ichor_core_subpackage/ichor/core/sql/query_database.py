from pathlib import Path
from typing import Union, List, Tuple
from sqlalchemy import select
from sqlalchemy import func
import sqlalchemy
from ichor.core.sql import Dataset, Points, AtomNames
from sqlalchemy import create_engine
import pandas as pd
from ichor.core.atoms import Atom, Atoms
from ichor.core.common.str import get_characters
from ichor.core.calculators import calculate_alf_features, calculate_alf_atom_sequence
from ichor.core.common.constants import multipole_names, spherical_monopole_labels, \
    spherical_dipole_labels, spherical_quadrupole_labels, spherical_octupole_labels, \
        spherical_hexadecapole_labels
from ichor.core.multipoles import rotate_dipole, rotate_quadrupole, rotate_octupole, rotate_hexadecapole
from ichor.core.atoms import ALF
from ichor.core.models.gaussian_energy_derivative_wrt_features import form_b_matrix, convert_to_feature_forces
from sqlalchemy.orm import Session
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection


def rotate_multipole_moments(row_with_atom_info, C):

        local_spherical_multipoles = {spherical_monopole_labels[0]: row_with_atom_info["q00"].item()}

        local_dipole_moments = rotate_dipole(
            *(
                row_with_atom_info[dipole_label].item()
                for dipole_label in spherical_dipole_labels
            ),
            C,
        )
        for dipole_name, dipole_value in zip(
            spherical_dipole_labels, local_dipole_moments
        ):
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

def create_db_engine(db_path: Union[str, Path], echo=False) -> sqlalchemy.engine.Engine:
    """Creates an engine to a SQLite3 database and returns the Engine object.

    :param db_path: Path to SQLite3 database
    :param echo: Whether to echo SQL queries, defaults to False
    :return: An egnine object for the SQL database
    :rtype: sqlalchemy.engine.Engine
    """
    database_path = str(Path(db_path).absolute())
    # create database engine and start session
    engine = create_engine(f"sqlite+pysqlite:///{database_path}", echo=echo, future=True)
    
    return engine

def create_db_connection(db_path: Union[str, Path], echo=False) -> sqlalchemy.engine.Connection:
    """Creates a connection to a SQLite3 database and returns a connection object to be used
        when executing SQL statements with pandas.

    :param db_path: Path to SQLite3 database
    :param echo: Whether to echo SQL queries, defaults to False
    :return: A connection object to the SQL database
    :rtype: sqlalchemy.engine.Connection
    """
    
    database_path = str(Path(db_path).absolute())

    # create database engine and start session
    engine = create_engine(f"sqlite+pysqlite:///{database_path}", echo=echo, future=True)
    conn = engine.connect()
    
    return conn


def raw_one_atom_data_to_df(db_path: Union[str, Path], atom_name: str, integration_error: float = 0.001,
                         echo=False, drop_irrelevant_cols=True) -> pd.DataFrame:
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
    
    conn = create_db_connection(db_path, echo=echo)
        
    stmt = (select(Points, Dataset, AtomNames)
                .join(Points)
                .join(AtomNames)
                .where(func.abs(Dataset.integration_error) < integration_error)
                .where(AtomNames.name == atom_name)
                )
    
    df = pd.read_sql(stmt, conn)
    
    # drop columns which contain IDs and other things from SQLAlchemy query
    if drop_irrelevant_cols:
        df = df.drop(["id", "id_1", "point_id", "atom_id", "name_1", "id_2"], axis="columns")
    
    return df

def write_raw_one_atom_data_to_csv(db_path: Union[str, Path], atom_name: str, integration_error: float = 0.001,
                         echo=False, drop_irrelevant_cols=True):
    """Saves the raw data for one atom as stored in the SQLite3 database to a csv file.

    :param db_path: Path or str to SQLite3 database
    :param atom_name: string of atom name (e.g. `C1`)
    :param integration_error: Integration error for AIMAll. Any point with a higher
        absolute integration error will not be selected, defaults to 0.001
    :param echo: Whether to echo the executed SQL queries, defaults to False
    :param drop_irrelevant_cols: Whether to drop irrelevant columns (id columns that do not contain data)
        from the DataFrame, defaults to True
    """

    df = raw_one_atom_data_to_df(db_path, atom_name, integration_error, echo, drop_irrelevant_cols)
    df.to_csv(f"raw_db_data_{atom_name}.csv")

def get_list_of_point_ids_from_db(db_path: Union[str, Path], echo=False) -> List[str]:
    """Returns a list of all the point names in the database

    :param db_path: Path or string to database
    :param echo: Whether to echo SQL queries, defaults to False
    :return: List of strings of the point names
    """
    conn = create_db_connection(db_path, echo=echo)

    stmt = select(Points)
    df = pd.read_sql(stmt, conn)
    
    return list(df["id"])

def get_list_of_atom_names_from_db(db_path: Union[str, Path], echo=False) -> List[str]:
    """Returns a list of all the point names in the database

    :param db_path: Path or string to database
    :param echo: Whether to echo SQL queries, defaults to False
    :return: List of strings of the atom names
    """
    conn = create_db_connection(db_path, echo=echo)

    stmt = select(AtomNames)
    df = pd.read_sql(stmt, conn)
    
    return list(df["name"])

def get_full_dataframe_for_all_atoms(db_path: Union[str, Path],  echo=False) -> pd.DataFrame:
    """Returns a dataframe containing all the data for all atoms

    :param db_path: Path or str to database
    :param echo: Whether to echo SQL statements, defaults to False
    :return: A pandas dataframe containing information for all atoms
    """
    
    conn = create_db_connection(db_path=db_path, echo=echo)
    
    stmt =  (select(Points, Dataset, AtomNames)
                .join(Dataset, Dataset.point_id == Points.id)
                .join(AtomNames, Dataset.atom_id == AtomNames.id)
    )
    # do not check integration error here, just always get full df with all atoms
                # .where(func.abs(Dataset.integration_error) < integration_error)
                # )

    full_df = pd.read_sql(stmt, conn)

    return full_df


def get_alf_from_first_db_geometry(db_path: Union[str, Path], echo=False) -> List[ALF]:
    """Returns the atomic local frame for every atom from the first point.

    :param db_path: Path to SQLite3 database containing `Points`, `AtomNames`, and `Dataset` tables.
    :param echo: Whether to echo executed SQL queries, defaults to False
    :return: A list of ALF instances for every atom in the system.
    """
    
    first_point_id = get_list_of_point_ids_from_db(db_path=db_path, echo=echo)[0]
    full_df = get_full_dataframe_for_all_atoms(db_path=db_path, echo=echo)
        
    atoms = Atoms()
        
    one_point_df = full_df.loc[full_df["id"] == first_point_id]
        
    for row_id, row_data in one_point_df.iterrows():
        atom_type = get_characters(row_data.name_1)
        atoms.append(Atom(atom_type, row_data.x, row_data.y, row_data.z))
        
    return atoms.alf_list(calculate_alf_atom_sequence)


def write_processed_one_atom_data_to_csv(full_df: pd.DataFrame, point_ids: List[int],
                                         atom_name: str, alf: List[ALF],
                                         max_integration_error = 0.001,
                                         write_index_col=False):
    """Writes features, iqa energy, as well as rotated multipole moments (given an ALF) to a csv file
    for all points (as long as integration error for the atom of interest is below a threshold integration error).

    :param full_df: DataFrame object extracted from SQLite database. This object contains information for
        all points (and all atoms in every point)
    :param point_ids: A list of integers represending the `id` column of the points table of the SQLite database.
    :param atom_name: The atom for which features, local multipole moments,
        as well as local forces are going to be calculated for every point in the dataset
    :param alf: A list of ALF instance to be used when calculating features
        and calculating C matrices
    :param max_integration_error: Maximum integration error that a point needs to have for the atom
        of interest. Having a higher (absolute) integration error for the atom of interest means that
        this point will not be added in the dataset for the atom of interest. However, the same
        point can be added in the dataset for another atom, if the integration error is good, defaults to 0.001
    """

    # final dictionary that is going to be converted to pd.DataFrame and written to csv
    total_dict = {}

    # loop over points
    for point_id in point_ids:
        
        # find geometry which matches the id
        one_point_df = full_df.loc[full_df["id"] == point_id]

        # check that integration error is below threshold, otherwise do not calculate features
        # for the atom and do not add this point to training set for this atom.
        # if other atoms have good integration errors, the same point can be used in their training sets.
        row_with_atom_info = one_point_df.loc[one_point_df['name_1'] == atom_name]

        if not one_point_df["force_x"].isnull().values.any():
            global_forces_array = one_point_df[["force_x", "force_y", "force_z"]].to_numpy()
        else:
            global_forces_array = None

        # If the atomic information (.int file) was missing, then this
        # iqa energy will be None, so it will not get executed
        if row_with_atom_info["iqa"].item():

            # if the absolute of the integration error is less than threshold, then calculate features
            if abs(row_with_atom_info["integration_error"].item()) < max_integration_error:

                # create atoms instance which will be used to calculate features
                atoms = Atoms()
                for row_id, row_data in one_point_df.iterrows():
                    # atoms accepts atom type (but database contains the atom index as well)
                    atom_type = get_characters(row_data.name_1)
                    atoms.append(Atom(atom_type, row_data.x, row_data.y, row_data.z))

                C = atoms[atom_name].C(alf)
                central_atom_index = atoms[atom_name].i # 0-indexed
                # calculate features for the atom of interest
                one_atom_features = atoms[atom_name].features(calculate_alf_features, alf)
                n_features = len(one_atom_features)

                if global_forces_array is not None:
                    b_matrix = form_b_matrix(atoms, alf, central_atom_index)
                    negative_dE_df = convert_to_feature_forces(global_forces_array, b_matrix, alf, central_atom_index)
                else:
                    negative_dE_df = [None] * n_features

                # make dictionary of rotated multipoles
                local_spherical_multipoles = rotate_multipole_moments(row_with_atom_info, C)

                # add the point_id and name of point to dictionary
                point_id_str = str(point_id)
                total_dict[point_id_str] = {"point_id": point_id, "point_name": row_with_atom_info["name"].item()}
                # add features to dictionary               
                total_dict[point_id_str].update({f"f{i}": one_atom_feature for i, one_atom_feature in zip(range(1, n_features+1), one_atom_features)})
                # add wfn energy to dictionary
                total_dict[point_id_str].update({"wfn_energy": row_with_atom_info["wfn_energy"].item()})
                # add -dE/df (forces wrt features) to dict
                total_dict[point_id_str].update({f"-dE/df{i}": neg_dE_df for i, neg_dE_df in zip(range(1, n_features+1), negative_dE_df)})
                # add iqa to dictionary
                total_dict[point_id_str].update({"iqa": row_with_atom_info["iqa"].item()})
                total_dict[point_id_str].update(local_spherical_multipoles)

        else:

            # create atoms instance which will be used to calculate features
            atoms = Atoms()
            for row_id, row_data in one_point_df.iterrows():
                # atoms accepts atom type (but database contains the atom index as well)
                atom_type = get_characters(row_data.name_1)
                atoms.append(Atom(atom_type, row_data.x, row_data.y, row_data.z))

            C = atoms[atom_name].C(alf)
            central_atom_index = atoms[atom_name].i # 0-indexed
            # calculate features for the atom of interest
            one_atom_features = atoms[atom_name].features(calculate_alf_features, alf)
            n_features = len(one_atom_features)

            if global_forces_array is not None:
                b_matrix = form_b_matrix(atoms, alf, central_atom_index)
                negative_dE_df = convert_to_feature_forces(global_forces_array, b_matrix, alf, central_atom_index)
            else:
                negative_dE_df = [None] * n_features
            # add the point_id and name of point to dictionary
            point_id_str = str(point_id)
            total_dict[point_id_str] = {"point_id": point_id, "point_name": row_with_atom_info["name"].item()}
            # add features to dictionary               
            total_dict[point_id_str].update({f"f{i}": one_atom_feature for i, one_atom_feature in zip(range(1, n_features+1), one_atom_features)})
            # add wfn energy to dictionary
            total_dict[point_id_str].update({"wfn_energy": row_with_atom_info["wfn_energy"].item()})
            # add -dE/df (forces wrt features) to dict
            total_dict[point_id_str].update({f"-dE/df{i}": neg_dE_df for i, neg_dE_df in zip(range(1, n_features+1), negative_dE_df)})

    alf_for_current_atom = alf[central_atom_index]
    alf_str = "alf_" + "_".join(list(map(str, alf_for_current_atom)))

    # write the total dict containing information for all points to a DataFrame and save
    total_df = pd.DataFrame.from_dict(total_dict, orient="index")
    total_df.to_csv(f"{atom_name}_processed_data_{alf_str}.csv", index=write_index_col)

def get_db_information(db_path: Union[str, Path], echo=False) -> Tuple[List[str], List[str], pd.DataFrame]:
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
    point_ids = get_list_of_point_ids_from_db(db_path=db_path, echo=echo)
    # get atom names to loop over
    atom_names = get_list_of_atom_names_from_db(db_path, echo=echo)
    # full dataframe contains all atoms/points below some integration error
    full_df = get_full_dataframe_for_all_atoms(db_path=db_path, echo=echo)
    
    return point_ids, atom_names, full_df


def write_processed_data_for_atoms(db_path: Union[str, Path], alf: List[ALF],
                                   max_integration_error: float = 0.001,
                                   write_index_col=False,
                                   echo=False,
                                   atom_names: List = None,
                                   ):
    """Writes a csv containing the features, wfn energy, -dE/df (note that these are forces wtr features),
        iqa energy, and rotated multipoles for every atom in the SQL database.
        Note that only points for which the absolute integration error for the atom of interest
        is below the threshold are added to the
        corresponding atomic datasets. 

    :param db_path: Path to SQLite3 database containing `Points`, `AtomNames`, and `Dataset` tables.
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
    
    point_ids, all_atom_names, full_df = get_db_information(db_path, echo=echo)
    
    if not atom_names:
        atom_names = all_atom_names

    for atom_name in atom_names:

        write_processed_one_atom_data_to_csv(full_df, point_ids, atom_name=atom_name, alf=alf,
                                             max_integration_error=max_integration_error,
                                             write_index_col=write_index_col)

def atoms_from_point_id(full_df, point_id: int) -> "Atoms":
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
        atom_type = get_characters(row_data.name_1)
        atoms.append(Atom(atom_type, row_data.x, row_data.y, row_data.z))

    return atoms

def delete_points_by_id(engine, point_ids: List[int]):

    @event.listens_for(Engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, SQLite3Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()

    session = Session(engine, future=True)
    session.query(Points).filter(Points.id.in_(point_ids)).delete()
    session.commit()