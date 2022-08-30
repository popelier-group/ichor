from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from typing import Union
from pathlib import Path

def create_database(database_path: Union[str, Path]):
    """Creates empty database in which important information from a PointsDirectory instance can be stored.

    :param database_path: A string or Path to a (non-existing) database on disk.
    """
        
    database_path = str(Path(database_path))

    # create new database and start session
    engine = create_engine(f"sqlite+pysqlite://{database_path}", echo=True, future=True)
    # Session = sessionmaker(bind=engine)
    # session = Session()
    Base = declarative_base()

    #####
    # Declare structure of database
    #####

    class AtomNames(Base):
        
        __tablename__ = "atom_names"

        id = Column(Integer, primary_key=True)
        name = Column(String, unique=True, nullable=False)
        
        children = relationship("Dataset", backref="atom_names")

    class Points(Base):
        
        __tablename__ = "points"
        
        id = Column(Integer, primary_key=True)
        date_added = Column(String, nullable=False)
        name = Column(String, nullable=False)
        wfn_energy = Column(Float, nullable=False)
        
        children = relationship("Dataset", backref="points")
        
    class Dataset(Base):
        
        __tablename__ = "dataset"
        
        id = Column(Integer, primary_key=True)
        point_id = Column(Integer, ForeignKey("points.id"))
        atom_id = Column(Integer, ForeignKey("atom_names.id"))
        x = Column(Float, nullable=False)
        y = Column(Float, nullable=False)
        z = Column(Float, nullable=False)
        force_x = Column(Float, nullable=True)
        force_y = Column(Float, nullable=True)
        force_z = Column(Float, nullable=True)
        iqa_energy = Column(Float, nullable=True)
        integration_error = Column(Float, nullable=True)
        q00 = Column(Float, nullable=True)
        q10 = Column(Float, nullable=True)
        q11c = Column(Float, nullable=True)
        q11s = Column(Float, nullable=True)
        q20 = Column(Float, nullable=True)
        q21c = Column(Float, nullable=True)
        q21s = Column(Float, nullable=True)
        q22c = Column(Float, nullable=True)
        q22s = Column(Float, nullable=True)
        q30 = Column(Float, nullable=True)
        q31c = Column(Float, nullable=True)
        q31s = Column(Float, nullable=True)
        q32c = Column(Float, nullable=True)
        q32s = Column(Float, nullable=True)
        q33c = Column(Float, nullable=True)
        q33s = Column(Float, nullable=True)
        q40 = Column(Float, nullable=True)
        q41c = Column(Float, nullable=True)
        q41s = Column(Float, nullable=True)
        q42c = Column(Float, nullable=True)
        q42s = Column(Float, nullable=True)
        q43c = Column(Float, nullable=True)
        q43s = Column(Float, nullable=True)
        q44c = Column(Float, nullable=True)
        q44s = Column(Float, nullable=True)

    # create the table on disk
    Base.metadata.create_all(engine)