from pathlib import Path
from typing import Union, List, Dict, Tuple
from sqlalchemy import select
from sqlalchemy import func
import sqlalchemy
from ichor.core.sql import Dataset, Points, AtomNames
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
from ichor.core.atoms import Atom, Atoms
from ichor.core.common.str import get_characters
from ichor.core.calculators import calculate_alf_features, calculate_alf_atom_sequence
from ichor.core.common.constants import multipole_names, spherical_monopole_labels, \
    spherical_dipole_labels, spherical_quadrupole_labels, spherical_octupole_labels, \
        spherical_hexadecapole_labels
from ichor.core.multipoles import rotate_dipole, rotate_quadrupole, rotate_octupole, rotate_hexadecapole
from ichor.core.atoms import ALF

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


def get_alf_from_first_db_geometry(db_path: Union[str, Path], echo=False) -> Dict[str, ALF]:
    """Returns the atomic local frame for every atom from the first point.

    :param db_path: Path to SQLite3 database containing `Points`, `AtomNames`, and `Dataset` tables.
    :param echo: Whether to echo executed SQL queries, defaults to False
    :return: A dictionary of key(atom_name), val(ALF instance, a named tuple)
    """
    
    first_point_id = get_list_of_point_ids_from_db(db_path=db_path, echo=echo)[0]
    full_df = get_full_dataframe_for_all_atoms(db_path=db_path, echo=echo)
        
    atoms = Atoms()
        
    one_point_df = full_df.loc[full_df["id"] == first_point_id]
        
    for row_id, row_data in one_point_df.iterrows():
        atom_type = get_characters(row_data.name_1)
        atoms.append(Atom(atom_type, row_data.x, row_data.y, row_data.z))
        
    return atoms.alf_dict(calculate_alf_atom_sequence)


def write_processed_one_atom_data_to_csv(full_df: pd.DataFrame, point_ids: List[int],
                                         atom_name: str, alf: Dict[str, ALF],
                                         max_integration_error = 0.001,
                                         write_index_col=False):
    """Writes features, iqa energy, as well as rotated multipole moments (given an ALF) to a csv file
    for all points (as long as integration error for the atom of interest is below a threshold integration error).

    :param full_df: DataFrame object extracted from SQLite database. This object contains information for
        all points (and all atoms in every point)
    :param point_ids: A list of integers represending the `id` column of the points table of the SQLite database.
    :param atom_name: The atom for which features, local multipole moments,
        as well as local forces are going to be calculated for every point in the dataset
    :param alf: A dictionary of key(atom_name):value(ALF instance) to be used when calculating features
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

        # if the absolute of the integration error is less than threshold, then calculate features
        if abs(row_with_atom_info["integration_error"].item()) < max_integration_error:

            # create atoms instance which will be used to calculate features
            atoms = Atoms()
            for row_id, row_data in one_point_df.iterrows():
                # atoms accepts atom type (but database contains the atom index as well)
                atom_type = get_characters(row_data.name_1)
                atoms.append(Atom(atom_type, row_data.x, row_data.y, row_data.z))

            # calculate features for the atom of interest
            C = atoms[atom_name].C(alf)
            one_atom_features = atoms[atom_name].features(calculate_alf_features, alf)
            n_features = len(one_atom_features)

            # default values to be written if forces do not exist
            local_forces_array = None, None, None
            # if forces are also in database then calculate local forces
            if row_with_atom_info["force_x"] is not None:

                global_forces_array = np.array([row_with_atom_info["force_x"].item(),
                                row_with_atom_info["force_y"].item(),
                                row_with_atom_info["force_z"].item()])
                
                local_forces_array = np.matmul(C, global_forces_array)
            
            # make dictionary of rotated multipoles
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
            
            # add features to dictionary               
            total_dict[str(point_id)] = {f"f{i}": one_atom_feature for i, one_atom_feature in zip(range(1, n_features+1), one_atom_features)}
            # add iqa to dictionary
            total_dict[str(point_id)].update({"iqa_energy": row_with_atom_info["iqa_energy"].item()})
            # add local forces after rotation or None if they were not calculated.
            total_dict[str(point_id)].update({"force_x": local_forces_array[0]})
            total_dict[str(point_id)].update({"force_y": local_forces_array[1]})
            total_dict[str(point_id)].update({"force_z": local_forces_array[2]})
            # add rotated multipole moments to dictionary
            total_dict[str(point_id)].update(local_spherical_multipoles)

    alf_for_current_atom = alf[atom_name]
    alf_str = "alf" + "_".join(list(map(str, alf_for_current_atom)))

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


def write_processed_data_for_atoms(db_path: Union[str, Path], alf: Dict[str, ALF],
                                   max_integration_error: float = 0.001,
                                   write_index_col=False,
                                   echo=False):
    """Writes a csv containing the features, iqa energy, and rotated multipoles for every atom in the SQL database.
        Note that only points for which the absolute integration error for the atom of interest
        is below the threshold are added to the
        corresponding atomic datasets. 

    :param db_path: Path to SQLite3 database containing `Points`, `AtomNames`, and `Dataset` tables.
    :param alf: A dictionary of key(atom_name):value(ALF instance) to be used when calculating features
        and calculating C matrices
    :param max_integration_error: Maximum integration error that a point needs to have for the atom
        of interest. Having a higher (absolute) integration error for the atom of interest means that
        this point will not be added in the dataset for the atom of interest. However, the same
        point can be added in the dataset for another atom, if the integration error is good, defaults to 0.001
    :param write_index_col: Whether to write the index col in the final .csv file, defaults to False
    :param echo: Whether to echo executed SQL statements, defaults to False
    """
    
    point_ids, atom_names, full_df = get_db_information(db_path, echo=echo)
    
    for atom_name in atom_names:

        write_processed_one_atom_data_to_csv(full_df, point_ids, atom_name=atom_name, alf=alf,
                                             max_integration_error=max_integration_error,
                                             write_index_col=write_index_col)
        