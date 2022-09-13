from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from typing import Union
from pathlib import Path

Base = declarative_base()

#####
# Declare structure of database
#####

class AtomNames(Base):
    
    __tablename__ = "atom_names"

    id = Column(Integer, primary_key=True)
    # these should not be nullable as a PointsDirectory should at least contain geometries
    # even if no jobs are ran yet
    name = Column(String, unique=True, nullable=False)

    children = relationship("Dataset", back_populates="atom_names_parent")

class Points(Base):
    
    __tablename__ = "points"
    
    id = Column(Integer, primary_key=True)
    date_added = Column(String, nullable=False)
    name = Column(String, nullable=False)
    # make nullable because Gaussian might not be ran yet
    wfn_energy = Column(Float, nullable=True)
    
    children = relationship("Dataset", back_populates="points_parent")
    
class Dataset(Base):
    
    __tablename__ = "dataset"
    
    id = Column(Integer, primary_key=True)
    point_id = Column(Integer, ForeignKey("points.id"))
    atom_id = Column(Integer, ForeignKey("atom_names.id"))
    
    points_parent = relationship("Points", back_populates="children")
    atom_names_parent = relationship("AtomNames", back_populates="children")
    
    # coordinates should exist even if jobs are not ran yet in a PointsDirectory
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    z = Column(Float, nullable=False)
    
    # forces might not exist (if Gaussian has not been ran or force keyword has not been used)
    # so make nullable
    force_x = Column(Float, nullable=True)
    force_y = Column(Float, nullable=True)
    force_z = Column(Float, nullable=True)
    
    # AIMAll might not have been ran yet or lower encomp settings used
    # so make nullable
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
    q50 = Column(Float, nullable=True)
    q51c = Column(Float, nullable=True)
    q51s = Column(Float, nullable=True)
    q52c = Column(Float, nullable=True)
    q52s = Column(Float, nullable=True)
    q53c = Column(Float, nullable=True)
    q53s = Column(Float, nullable=True)
    q54c = Column(Float, nullable=True)
    q54s = Column(Float, nullable=True)
    q55c = Column(Float, nullable=True)
    q55s = Column(Float, nullable=True)

def create_database(database_path: Union[str, Path], echo=False):
    """Creates empty database in which important information from a PointsDirectory instance can be stored.

    :param database_path: A string or Path to a (non-existing) database on disk.
    """

    database_path = str(Path(database_path).absolute())

    # create new database and start session
    engine = create_engine(f"sqlite+pysqlite:///{database_path}", echo=echo, future=True)
    # Session = sessionmaker(bind=engine)
    # session = Session()

    # create the table on disk
    Base.metadata.create_all(engine)