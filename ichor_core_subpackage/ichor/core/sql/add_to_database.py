from ichor.core.sql import AtomNames, Points, Dataset
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from datetime import datetime
from typing import List
from sqlalchemy import select
from ichor.core.common.constants import multipole_names
import warnings
from sqlalchemy.orm import Session

def create_database_session(database_path: Path, echo=False):
    """Creates a sqlalchemy Engine object as well as a Session object
    which are used to interact with the SQLite database.

    :param database_path: pathlib.Path object to database
    :param echo: Whether for SQLAlchemy to echo SQL commands used, defaults to False
    """

    database_path = str(Path(database_path).absolute())
    # create new database and start session
    engine = create_engine(f"sqlite+pysqlite:///{database_path}", echo=echo, future=True)
    Session = sessionmaker(bind=engine)
    session = Session()

    return session

def add_atom_names_to_database(session: Session, atom_names: List[str], echo=False):
    """Adds a list of atom names to the atom_names table of the database.

    :param database_path: Path to database
    :param atom_names: A list of atom names, e.g. ["C1", "H2", "H3", ....]
    """

    db_atom_names_list = [AtomNames(name=atom_name) for atom_name in atom_names]
    session.bulk_save_objects(db_atom_names_list)
    session.commit()

# TODO: make this more robust as some data might be absent. Check that .wfn exists before adding wfn data
# TODO: check that gaussian out forces exist. Check that int file exists.
def add_point_to_database(session: Session, point: "PointDirectory", echo=False, print_missing_data=True):
    """Adds information from an instance of a PointDirectory to the database.

    :param database_path: Path to database
    :param point: A PointDirectory instance, containing Gaussian/AIMAll outputs that can be
        written to the database.

    .. note:: Even if atomic data (.int file) is missing for a particular atom in the system,
        the information for the point will still be added to the database. This is because
        the rest the point can still be used in the training set for the other atoms.
    """

    # check for .sh file in directory as AIMALL should delete it if it ran successfully
    # if .sh file is found then do not append this point to the database as it can cause problems
    # when reading the database

    for _f in point.path.iterdir():
        if _f.suffix == ".sh":
            print(f"A shell file (.sh) was found in {point.path.absolute()}, so AIMAll probably crashed. Not added to db.")
            return
    
    ###############################
    # wfn information 
    ###############################
    
    # if wfn file exists
    if point.wfn:
        # ORM for points table
        db_point = Points(date_added=datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
                    name=point.name, wfn_energy=point.wfn.total_energy)
    # if file does not exist, still add to database, but do not contain wfn information
    else:
        # ORM for points table
        db_point = Points(date_added=datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
                        # wfn energy might not exist if Gaussian has not been ran yet (or wfn file does not exist.)
                        # add a None for wfn energy if wfn energy is not present
                    name=point.name, wfn_energy=None)
        if print_missing_data:
            print(f"Point {point.path} does not contain a Gaussian wavefunction (.wfn) file.")

    ###############################
    # gaussian output file check 
    ###############################
    
    if not point.gaussian_out:
        if print_missing_data:
            print(f"Point {point.path} does not contain a Gaussian output (.gau) file.")

    ###############################
    # _atomicfiles directory check 
    ###############################
        
    if not point.ints:

        if print_missing_data:
            print(f"Point {point.path} does not contain an atomicfiles directory (containing AIMAll .int).")
    
    # add database point to session. Need to do this before adding the dataset stuff
    # because the id needs to be assigned to the point (because dataset contains foreign key point_id)
    session.add(db_point)

    # use this list later to bulk add all Dataset instances to database
    # there are multiple Dataset instances because each single point (one row in points table)
    # relates to multiple rows in the dataset table (because one point contains many atoms and each atom has information for it)
    db_dataset_list = []

    # list that will add missing int files (if _atomicfiles directory exists) but .int file for an atom does not.
    missing_int_files = []

    # add information to dataset table for each atom
    for atom_name in point.atom_names:
        
        # make select statement to get atom name
        atom_select_statement = select(AtomNames).where(AtomNames.name == atom_name)
        # get the id of the atom from the atom_names table.
        # use scalars instead of execute and return the first row (there should be one row as atom names are unique)
        atom_id = session.scalars(atom_select_statement).first().id
        
        # get x, y, z coordinates of atom which can then be used to calculated features
        # based on the coordinates of the other atoms in the molecule
        atom_coordinates = point[atom_name].coordinates
        x_coord = atom_coordinates[0]
        y_coord = atom_coordinates[1]
        z_coord = atom_coordinates[2]
        
        ###############################
        # .gau / gaussian output information
        ###############################

        # forces are saved directly from gaussian out file, thus they are in
        # global cartesian coordinates. This means these forces need to be rotated later
        # when an ALF is chosen for atoms.
        if point.gaussian_out:
            if point.gaussian_out.global_forces:
                atom_global_forces = point.gaussian_out.global_forces[atom_name]
                atom_force_x = atom_global_forces.x
                atom_force_y = atom_global_forces.y
                atom_force_z = atom_global_forces.z

            # in case that the force keyword was not used but gaussian out exists
            else:
                atom_force_x, atom_force_y, atom_force_z = None, None, None
                print(f"Point {point.path} does not have forces in Gaussian output (.gau) file.")
        # in case that gaussian out does not exist in point directory
        else:
            atom_force_x, atom_force_y, atom_force_z = None, None, None
            
        ###############################
        # .int file information 
        ###############################
        if point.ints:
            # add information from int file for the current atom
            # get the INT instance representing the .int file for the atom
            # use get here to get a default value of None if .int file is missing for some atom
            atom_int_file = point.ints.get(atom_name, None)
            
            # if .int file / INT instance exists, then data can be read in
            if atom_int_file:

                # do not display warning from .int file if iqa energy is not there
                # iqa energy will not be in an existing .int file in -encomp setting is below 3
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore")
                    atom_iqa_energy = atom_int_file.iqa

                # integration error should always exist
                atom_integration_error = atom_int_file.integration_error

                # note that these are not rotated because the alf has not been chosen yet
                # the user can choose an alf and rotate the global spherical multipoles as needed
                global_multipole_moments = atom_int_file.global_spherical_multipoles

                # add the Dataset object to list so it can be bulk written later
                db_dataset_list.append(Dataset(point_id=db_point.id,
                                        atom_id=atom_id,
                                        x=x_coord,
                                        y=y_coord,
                                        z=z_coord,
                                        force_x=atom_force_x,
                                        force_y=atom_force_y,
                                        force_z=atom_force_z,
                                        iqa=atom_iqa_energy,
                                        integration_error=atom_integration_error,
                                        **global_multipole_moments
                                        )
                )
            
            # if .int file for an atom does not exist then (but _atomicfiles directory exists)
            # then just append the coordinates and any other read in information
            else:
                # add the Dataset object to list so it can be bulk written later
                db_dataset_list.append(Dataset(point_id=db_point.id,
                                        atom_id=atom_id,
                                        x=x_coord,
                                        y=y_coord,
                                        z=z_coord,
                                        force_x=atom_force_x,
                                        force_y=atom_force_y,
                                        force_z=atom_force_z,
                                        # the .int file arguments will be None by default
                                        # as they can be nullable because of the dataset SQL table definition
                                        )
                                    )
                missing_int_files.append(atom_name)

        else:
            # add the Dataset object to list so it can be bulk written later
            db_dataset_list.append(Dataset(point_id=db_point.id,
                                    atom_id=atom_id,
                                    x=x_coord,
                                    y=y_coord,
                                    z=z_coord,
                                    force_x=atom_force_x,
                                    force_y=atom_force_y,
                                    force_z=atom_force_z,
                                    # the .int file arguments will be None by default
                                    # as they can be nullable because of the dataset SQL table definition
                                    )
                                )
            
    # if there are missing atoms, then print these out
    if len(missing_int_files) > 0:
        
        if print_missing_data:
            print(f"Point {point.path} has missing .int files for atoms: {missing_int_files}.")

    # bulk save the information for all atoms in the point
    session.bulk_save_objects(db_dataset_list)
    # commit to database
    session.commit()