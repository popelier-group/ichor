from ichor.core.files.file import WriteFile
from typing import Union
from pathlib import Path
from ichor.core.analysis.geometry import get_internal_feature_indices
from ichor.core.constants import dlpoly_weights

class DlPolyField(WriteFile):
    
    def __init__(self, path: Union[Path, str],
                 atoms,
                 system_name: str,
                 nummols = 1,
                 
                 
                 ):
        super().__init__(path)
        
        self.atoms = atoms
        self.system_name = system_name
        self.nummols = nummols

    # TODO: implement reading for dlpoly field file
    # def _read_file(self):
    #     ...

    def _write_file(self):
        
        bonds, angles, dihedrals = get_internal_feature_indices(self.atoms)

        with open(self.path, "w") as f:
            f.write("DL_FIELD v3.00\n")
            f.write("Units kJ/mol\n")
            f.write("Molecular types 1\n")
            f.write(f"{self.system_name}\n")
            f.write(f"nummols {self.nummols}\n")
            f.write(f"atoms {len(self.atoms)}\n")
            for atom in self.atoms:
                f.write(
                    #  Atom Type      Atomic Mass                    Charge Repeats Frozen(0=NotFrozen)
                    f"{atom.type}\t\t{dlpoly_weights[atom.type]:.7f}     0.0   1   0\n"
                )
            f.write(f"BONDS {len(bonds)}\n")
            for i, j in bonds:
                f.write(f"harm {i} {j} 0.0 0.0\n")
            if len(angles) > 0:
                f.write(f"ANGLES {len(angles)}\n")
                for i, j, k in angles:
                    f.write(f"harm {i} {j} {k} 0.0 0.0\n")
            if len(dihedrals) > 0:
                f.write(f"DIHEDRALS {len(dihedrals)}\n")
                for i, j, k, l in dihedrals:
                    f.write(f"harm {i} {j} {k} {l} 0.0 0.0\n")
            f.write("finish\n")
            f.write("close\n")