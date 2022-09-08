from ichor.core.files.file import WriteFile
from typing import Union
from pathlib import Path

class DlPolyConfig(WriteFile):
    """Write out a DLPoly CONFIG file. The name of the file needs to be CONFIG,  so DL POLY knows to use it.
    """
    
    def __init__(self, path: Union[Path, str],
                 system_name,
                 atoms,
                 cell_size = 50):

        super().__init__(path)
        
        self.system_name = system_name
        self.atoms = atoms
        self.cell_size = cell_size
        # TODO: why is centering needed?
        # atoms.centre()

    # TODO: implement reading for dlpoly config file
    # def _read_file(self):
    #     ...

    def _write_file(self):

        with open(self.path , "w") as f:
            
            f.write("Frame :         1\n")
            f.write("\t0\t1\n")  # PBC Solution to temporary problem
            f.write(f"{self.cell_size} 0.0 0.0\n")
            f.write(f"0.0 {self.cell_size} 0.0\n")
            f.write(f"0.0 0.0 {self.cell_size}\n")
            for atom in self.atoms:
                f.write(
                    f"{atom.type}  {atom.index}  {self.system_name}_{atom.type}{atom.index}\n"
                )
                f.write(f"{atom.x}\t\t{atom.y}\t\t{atom.z}\n")