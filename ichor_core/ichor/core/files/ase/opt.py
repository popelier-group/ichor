from pathlib import Path
from typing import Optional, Union

from ichor.core.atoms import Atoms

from ichor.core.files.file import File, FileContents, ReadFile, WriteFile
from ichor.core.files.file_data import HasAtoms

_filetype = ".py" ## NOT SURE ON THIS

class XtbJobScript:
    def __init__(
        self,
        path: Union[Path, str],
        method: Optional[str] = None,
        solvent: Optional[str] = None,
        electronic_temperature: Optional[int] = None,
        max_iterations: Optional[int] = None,
        fmax: Optional[int] = None,
        calculator: Optional[str] = None, # Is calculator needed?
        atoms: Optional[Atoms] = None,
        

    ):
        File.__init__(self,path)

        self.method: str = method
        self.solvent: str = solvent 
        self.electronic_temperature: int = electronic_temperature 
        self.max_iterations: int = max_iterations 
        self.fmax: int = fmax 
        self.calculator: str = calculator
        self.atoms = atoms

        # Assumed no readfile class was needed?
        
    def set_write_defauts_if_needed(self):      # Used Bienfait's script inputs for defauls for now
        self.method = self.method or "GFN2-xTB"
        self.solvent = self.solvent or "none"
        self.electronic_temperature = self.electronic_temperature or 300
        self.max_iterations = self.max_iterations or 2048
        self.fmax = self.fmax or 0.01

    def _check_values_before_writing(self):
        """Basic checks done prior to writing file.

        .. note:: Not everything written to file can be checked for, so
        there is still the need for a user to check out what is being written.
        """

        if len(self.atoms) == 0:
            raise ValueError("There are no atoms to write to Xtb input file.")

    def _write_file(self, path: Path, *args, **kwargs):
        
        write_str += f"from ase.io import read\n" # Do we use ICHOR's ReadFile here or ase read?
        write_str += "from ase.optimize import BFGS\n"
        write_str += f"from ase.io import write\n"
        write_str += f"from xtb.ase.calculator import XTB\n"
        
        # Do we want to use ICHOR 'Atoms' class here to read in atoms
        # Or the ASE 

