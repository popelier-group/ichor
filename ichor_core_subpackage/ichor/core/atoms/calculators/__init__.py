from ichor.core.atoms.calculators.alf import (ALF, ALFCalculatorFunction,
                                              alf_calculators,
                                              calculate_alf_atom_sequence,
                                              calculate_alf_cahn_ingold_prelog,
                                              default_alf_calculator,
                                              get_atom_alf_from_list_of_alfs)
from ichor.core.atoms.calculators.c_matrix_calculator import calculate_c_matrix
from ichor.core.atoms.calculators.connectivity import default_connectivity_calculator
from ichor.core.atoms.calculators.features import (calculate_alf_features,
                                                   default_feature_calculator,
                                                   feature_calculators)
from typing import Callable, Union, List
from ichor.core.atoms import Atom, Atoms
import numpy as np



### functions for Atoms instance
def get_atoms_alf(alf_calculator: Union[List[ALF], Callable], atoms_instance: Atoms) -> List[ALF]:
    """ Returns either an ALF instance directly or uses a calculator function to calculate and return an ALF instance."""
    
    if all([isinstance(i, ALF) for i in alf_calculator]):
        return alf_calculator
    elif isinstance(alf_calculator, Callable):
        return [alf_calculator(atom_instance) for atom_instance in atoms_instance]

def get_atoms_c_matrix(alf_calculator: Union[List[ALF], Callable], atoms_instance: Atoms) -> np.ndarray:
    """ Calculates a C matrix given an ALF, or calculates an ALF first and then a C matrix."""

    if all([isinstance(i, ALF) for i in alf_calculator]):
        return [calculate_c_matrix(atoms_instance[alf[0]], alf) for alf in alf_calculator]
    elif isinstance(alf_calculator, Callable):
        return [calculate_c_matrix(alf_calculator(atom_instance)) for atom_instance in atoms_instance]

def get_atoms_connectivity(connectivity_calculator: Union[np.ndarray, Callable], atoms_instance: Atoms) -> np.ndarray:
    """ Returns passed in connectivity matrix  or calculates connectivity using a calculator function and returns connectivity."""
    
    n_atoms = atoms_instance.natoms
    
    if isinstance(connectivity_calculator, np.ndarray):
        if np.ndarray.shape == (n_atoms, n_atoms):
            return connectivity_calculator
        else:
            raise ValueError("The connectivity matrix for Atoms instance must be of dimension 2 and of shape `n_atoms x n_atoms`.")
    elif isinstance(connectivity_calculator, Callable):
        return connectivity_calculator(atoms_instance)

def get_atoms_features(feature_calculator: Union[List[ALF], Callable], atoms_instance: Atoms, **kwargs) -> np.ndarray:
    """ Returns features calculated for an Atoms instance given a list of ALFs, or calculates ALF first using a calculator function and then returns features."""

    if all([isinstance(i, ALF) for i in feature_calculator]):
        return np.array(atoms_instance[alf[0]].features(alf, **kwargs) for alf in feature_calculator)
    elif isinstance(feature_calculator, Callable):
        return np.array(atom_instance.features(feature_calculator, **kwargs) for atom_instance in atoms_instance)

def get_atoms_features_dict(feature_calculator: Union[List[ALF], Callable], atoms_instance: Atoms, **kwargs) -> np.ndarray:
    """ Returns features calculated for an Atoms instance given a list of ALFs, or calculates ALF first using a calculator function and then returns features."""

    if all([isinstance(i, ALF) for i in feature_calculator]):
        return {atoms_instance[alf[0]].name: atoms_instance[alf[0]].features(alf, **kwargs) for alf in feature_calculator}
    elif isinstance(feature_calculator, Callable):
        return {atom_instance.name: atom_instance.features(feature_calculator, **kwargs) for atom_instance in atoms_instance}


### functions for Atom instance
def get_atom_alf(alf_calculator: Union[ALF, Callable], atom_instance: Atom) -> ALF:
    """ Returns either an ALF instance directly or uses a calculator function to calculate and return an ALF instance."""
    
    if isinstance(alf_calculator, ALF):
        return alf_calculator
    elif isinstance(alf_calculator, Callable):
        return alf_calculator(atom_instance)
    else:
        raise TypeError(f"Cannot compute ALF from calculator type: {type(alf_calculator)}.")
    
def get_atom_c_matrix(alf_calculator: Union[ALF, Callable], atom_instance: Atom) -> np.ndarray:
    """ Calculates a C matrix given an ALF, or calculates an ALF first and then a C matrix."""

    if isinstance(alf_calculator, ALF):
        return calculate_c_matrix(atom_instance, alf_calculator)
    elif isinstance(alf_calculator, Callable):
        return calculate_c_matrix(alf_calculator(atom_instance))
    else:
        raise TypeError(f"Cannot compute C matrix from calculator type: {type(alf_calculator)}.")
    
def get_atom_connectivity(connectivity_calculator: Union[np.ndarray, Callable], atom_instance: Atoms) -> np.ndarray:
    """ Returns passed in connectivity matrix  or calculates connectivity using a calculator function and returns connectivity."""
    
    if isinstance(connectivity_calculator, np.ndarray):
        if connectivity_calculator.ndim == 1:
            return connectivity_calculator
        else:
            raise ValueError("The connectivity for a single atom must be a one dimensional array.")
    elif isinstance(connectivity_calculator, Callable):
        return atom_instance.parent.connectivity(connectivity_calculator)[atom_instance.i]
    else:
        raise TypeError(f"Cannot compute connectivity matrix from calculator type: {type(connectivity_calculator)}")

# TODO: make this work for different feature calculators. One way would be to pass in alf in kwargs
def get_atom_features(alf_calculator: Union[Callable, ALF], atom_instance: Atom, **kwargs) -> np.ndarray:
    """ Returns features calculated for one atom given an ALF, or calculates ALF first using a calculator function and then returns features."""

    if isinstance(alf_calculator, ALF):
        return calculate_alf_features(atom_instance, alf_calculator, **kwargs)
    elif isinstance(alf_calculator, Callable):
        return calculate_alf_features(atom_instance, alf_calculator(atom_instance), **kwargs)
    else:
        raise TypeError(f"Cannot compute features from calculator type: {type(alf_calculator)}")
