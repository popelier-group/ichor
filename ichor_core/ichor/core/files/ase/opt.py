from pathlib import Path
from typing import Optional, Union

from ichor.core.files.file import File, WriteFile


class XTB(WriteFile, File):
    _filetype = ".py"

    def __init__(
        self,
        path: Union[Path, str],
        input_xyz_path: Union[Path, str],
        output_xyz_path: Union[Path, str],
        traj_path: Union[Path, str],
        log_path: Union[Path, str],
        method: Optional[str] = None,
        solvent: Optional[str] = None,
        electronic_temperature: Optional[int] = None,
        max_iterations: Optional[int] = None,
        fmax: Optional[float] = None,
    ):
        File.__init__(self, path)

        self.input_xyz_path = str(input_xyz_path)
        self.output_xyz_path = str(output_xyz_path)
        self.traj_path = str(traj_path)
        self.log_path = str(log_path)
        self.method: str = method
        self.solvent: str = solvent
        self.electronic_temperature: int = electronic_temperature
        self.max_iterations: int = max_iterations
        self.fmax: float = fmax

    def set_write_defaults_if_needed(
        self,
    ):  # Used Bienfait's script inputs for defaults for now
        self.method = self.method or "GFN2-xTB"
        self.solvent = self.solvent or "none"
        self.electronic_temperature = self.electronic_temperature or 300
        self.max_iterations = self.max_iterations or 2048
        self.fmax = self.fmax or 0.01

    def _write_file(self, path: Path, *args, **kwargs):
        write_str = ""

        write_str += f"from ase.io import read\n"
        write_str += f"from ase.optimize import BFGS\n"
        write_str += f"from ase.io import write\n"
        write_str += f"from xtb.ase.calculator import XTB\n\n"

        write_str += f'atoms=read("{self.input_xyz_path}")\n\n'  # ADD INPUT FILE

        write_str += (
            f'xtb_calc = XTB(method="{self.method}",'
            f'solvent="{self.solvent}",'
            f"electronic_temperature={self.electronic_temperature},"
            f"max_iterations={self.max_iterations})\n\n"
        )

        write_str += f"atoms.calc = xtb_calc\n\n"

        write_str += f'optimizer = BFGS(atoms, trajectory="{self.traj_path}", logfile="{self.log_path}")\n'
        write_str += f"optimizer.run(fmax={self.fmax})\n\n"

        write_str += f'write("{self.output_xyz_path}", atoms)\n\n'

        # Is it necessary to print these & where will they print?
        #        write_str += f'print("Final energy:", atoms.get_potential_energy())\n'
        #        write_str += f'print("Final positions:\n", atoms.get_positions())\n'
        #        write_str += f'print("Final forces:\n", atoms.get_forces())\n'

        return write_str
