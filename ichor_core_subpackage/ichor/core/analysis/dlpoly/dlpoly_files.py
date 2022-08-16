from ichor.core.files.file import WriteFile
from ichor.core.common.io import convert_to_path
from typing import Union
from pathlib import Path
from ichor.core.atoms import Atoms
from ichor.core.analysis.geometry import get_internal_feature_indices
from ichor.core.constants import dlpoly_weights

class DlPolyControl(WriteFile):
    """Write out a DLPoly CONTROL file. The name of the file needs to be CONTROL,  so DL POLY knows to use it.
    """
    
    # https://www.ehu.eus/sgi/ARCHIVOS/dlpoly_man.pdf , section 5.1.1
    
    def __init__(self, path: Path,
                 system_name: str = None,
                 ensemble: str = "nvt",
                 thermostat: str = "hoover",
                 thermostat_settings: list = [0.04],
                 temperature = 0.0,
                 timestep = 0.001,
                 steps = 5000,
                 scale = 100,
                 cutoff = 8.0,
                 rvwd = 8.0,
                 dump = 1000,
                 trajectory_i = 0,
                 trajectory_j = 1,
                 trajectory_k = 0,
                 print_every = 1,
                 stats_every = 1,
                 job_time = 10000000,
                 close_time = 20000
                 
                 ):
        super().__init__()
        
        self.system_name = system_name
        self.ensemble = ensemble
        self.thermostat = thermostat
        self.thermostat_settings = thermostat_settings
        self.temperature = temperature
        self.timestep = timestep,
        self.steps = steps
        self.scale = scale
        self.cutoff = cutoff
        self.rvdw = rvwd
        self.dump = dump
        self.trajectory_i = trajectory_i
        self.trajectory_j = trajectory_j
        self.trajectory_k = trajectory_k
        self.print_every = print_every
        self.stats_every = stats_every
        self.job_time = job_time
        self.close_time = close_time
        
    # TODO: implement reading for dlpoly control file
    # def _read_file(self):
    #     ...

    def _write_file(self):
        
        with open(self.path, "w") as f:
            f.write(f"Title: {self.system_name}\n")
            f.write("\n")
            # ensemble nvt hoover f select NVT ensemble, type Nose-Hoover with thermostat
            # relaxation constant f in ps
            str_thermostat_settings = " ".join([i for i in self.thermostat_settings])
            f.write(f"ensemble {self.ensemble} {self.thermostat} {str_thermostat_settings}\n")
            f.write("\n")
            if int(self.temperature) == 0:
                f.write("temperature 0\n")
                f.write("\n")
                f.write("#perform zero temperature run (really set to 10K)\n")
                f.write("zero\n")
                f.write("\n")
            else:
                f.write(f"temperature {self.temperature}\n")
                f.write("\n")
            f.write("\n")
            # timestep in ps
            f.write(f"timestep {self.timestep}\n")
            # number of timesteps
            f.write(f"steps {self.steps}\n")
            # rescale system temperature every n steps during equilibration
            f.write(f"scale {self.scale}\n")
            f.write("\n")
            f.write(f"cutoff  {self.cutoff}\n")
            f.write(f"rvdw    {self.rvdw}\n")
            f.write("vdw direct\n")
            f.write("vdw shift\n")
            f.write("fflux cluster L1\n")
            f.write("\n")
            f.write(f"dump  {self.dump}\n")
            f.write(f"traj {self.trajectory_i} {self.trajectory_j} {self.trajectory_k}\n")
            f.write(f"print every {self.print_every}\n")
            f.write(f"stats every {self.stats_every}\n")
            f.write("fflux print 0 1\n")
            f.write(f"job time {self.job_time}\n")
            f.write(f"close time {self.close_time}\n")
            f.write("finish\n")

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

# TODO: move these to menus
# def link_models(path: Path, models: Models):
#     model_dir = path / "model_krig"
#     mkdir(model_dir)
#     for model in models:
#         ln(model.path.absolute(), model_dir)

# def setup_dlpoly_directory(
#     path: Path, atoms: Atoms, models: Models, temperature: float = 0.0
# ):
#     mkdir(path)
#     write_control(path, temperature=temperature)
#     write_config(path, atoms)
#     write_field(path, atoms)
#     link_models(path, models)

# def get_dlpoly_directories(models: List[Models]) -> List[Path]:
#     dlpoly_directories = []
#     for model in models:
#         dlpoly_directories.append(
#             FILE_STRUCTURE["dlpoly"]
#             / f"{model.system}{str(model.ntrain).zfill(4)}"
#         )
#     return dlpoly_directories


# @convert_to_path
# def setup_dlpoly_directories(
#     atoms: Atoms, models: List[Models], temperature: float = 0.0
# ) -> List[Path]:
#     dlpoly_directories = get_dlpoly_directories(models)
#     for dlpoly_dir, model in zip(dlpoly_directories, models):
#         setup_dlpoly_directory(
#             dlpoly_dir, atoms, model, temperature=temperature
#         )
#     return dlpoly_directories
