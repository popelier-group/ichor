from ichor.core.sql import create_database, AtomNames, Points, Dataset
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from typing import Union
from pathlib import Path
from datetime import datetime
from typing import List
from sqlalchemy import select

def add_atom_names_to_database(database_path: Path, atom_names: List[str]):
    
    database_path = str(Path(database_path).absolute())

    # create new database and start session
    engine = create_engine(f"sqlite+pysqlite:///{database_path}", echo=True, future=True)

    Session = sessionmaker(bind=engine)
    session = Session()
    
    db_atom_names_list = [AtomNames(name=atom_name) for atom_name in atom_names]
    session.bulk_save_objects(db_atom_names_list)
    session.commit()

# TODO: make this more robust as some data might be absent. Check that .wfn exists before adding wfn data
# TODO: check that gaussian out forces exist. Check that int file exists.
def add_point_to_database(database_path: Path, point: "PointDirectory"):

    database_path = str(Path(database_path).absolute())

    # create new database and start session
    engine = create_engine(f"sqlite+pysqlite:///{database_path}", echo=True, future=True)

    Session = sessionmaker(bind=engine)
    session = Session()
    
    db_point = Points(date_added=datetime.today().strftime("%Y-%m-%d %H:%M:%S:%f"),
                name=point.name, wfn_energy=point.wfn.total_energy)

    # add database point to session
    session.add(db_point)
    
    db_dataset_list = []
    
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
        
        # forces are saved directly from gaussian out file, thus they are in
        # global cartesian coordinates. This means these forces need to be rotated later
        # when an ALF is chosen for atoms.
        atom_global_forces = point.gaussian_out.global_forces[atom_name]
        atom_force_x = atom_global_forces.x
        atom_force_y = atom_global_forces.y
        atom_force_z = atom_global_forces.z
        
        atom_int_file = point.ints[atom_name]
        atom_iqa_energy = atom_int_file.iqa
        atom_integration_error = atom_int_file.integration_error
        
        global_multipole_moments = atom_int_file.global_spherical_multipoles
        atom_q00 = global_multipole_moments["q00"]
        atom_q10 = global_multipole_moments["q10"]
        atom_q11c = global_multipole_moments["q11c"]
        atom_q11s = global_multipole_moments["q11s"]
        atom_q20 = global_multipole_moments["q20"]
        atom_q21c = global_multipole_moments["q21c"]
        atom_q21s = global_multipole_moments["q21s"]
        atom_q22c = global_multipole_moments["q22c"]
        atom_q22s = global_multipole_moments["q22s"]
        atom_q30 = global_multipole_moments["q30"]
        atom_q31c = global_multipole_moments["q31c"]
        atom_q31s = global_multipole_moments["q31s"]
        atom_q32c = global_multipole_moments["q32c"]
        atom_q32s = global_multipole_moments["q32s"]
        atom_q33c = global_multipole_moments["q33c"]
        atom_q33s = global_multipole_moments["q33s"]
        atom_q40 = global_multipole_moments["q40"]
        atom_q41c = global_multipole_moments["q41c"]
        atom_q42c = global_multipole_moments["q42c"]
        atom_q42s = global_multipole_moments["q42s"]
        atom_q43c = global_multipole_moments["q43c"]
        atom_q43s = global_multipole_moments["q43s"]
        atom_q44c = global_multipole_moments["q44c"]
        atom_q44s = global_multipole_moments["q44s"]
    
    
        db_dataset_list.append(Dataset(point_id=db_point.id,
                                atom_id=atom_id,
                                x=x_coord,
                                y=y_coord,
                                z=z_coord,
                                force_x=atom_force_x,
                                force_y=atom_force_y,
                                force_z=atom_force_z,
                                iqa_energy=atom_iqa_energy,
                                integration_error=atom_integration_error,
                                q00=atom_q00,
                                q10=atom_q10,
                                q11c=atom_q11c,
                                q11s=atom_q11s,
                                q20=atom_q20,
                                q21c=atom_q21c,
                                q21s=atom_q21s,
                                q22c=atom_q22c,
                                q22s=atom_q22s,
                                q30=atom_q30,
                                q31c=atom_q31c,
                                q31s=atom_q31s,
                                q32c=atom_q32c,
                                q32s=atom_q32s,
                                q33c=atom_q33c,
                                q33s=atom_q33s,
                                q40=atom_q40,
                                q41c=atom_q41c,
                                q42c=atom_q42c,
                                q42s=atom_q42s,
                                q43c=atom_q43c,
                                q43s=atom_q43s,
                                q44c=atom_q44c,
                                q44s=atom_q44s)
        )
    
    # add all the dataset object to database
    session.bulk_save_objects(db_dataset_list)
    # commit to write to database
    session.commit()