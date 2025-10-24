import textwrap
from pathlib import Path
from string import Template
from typing import Optional, Union

from ichor.core.files.file import File, WriteFile


class MtdTrajScript(WriteFile, File):
    _filetype = ".py"

    def __init__(
        self,
        path: Union[Path, str],
        input_xyz_path: Union[
            Path,
            str,
        ],
        collective_variables: list[int] = None,
        timestep: Optional[float] = None,
        bias_factor: Optional[list[float]] = None,
        iterations: Optional[int] = None,
        temperature: Optional[float] = None,
        system_name: Optional[str] = None,
        calculator: Optional[str] = None,
        time_units: Optional[str] = None,
        dist_units: Optional[str] = None,
        energy_units: Optional[str] = None,
        height: Optional[list[float]] = None,
        pace: Optional[list[float]] = None,
        sigma: Optional[list[float]] = None,
        grid_min: Optional[list[str]] = None,
        grid_max: Optional[list[str]] = None,
        grid_bin: Optional[list[int]] = None,
        solvent: Optional[str] = None,
        kT: Optional[float] = None,
        properties: Optional[list[str]] = None,
        md_timestep: Optional[float] = None,
        md_friction: Optional[float] = None,
        md_communication: Optional[str] = None,
        md_runsteps: Optional[int] = None,
        md_freq_out: Optional[int] = None,
        md_interval: Optional[int] = None,
    ):

        File.__init__(self, path)

        self.input_xyz_path = Path(input_xyz_path)
        self.collective_variables: list[int] = collective_variables
        self.timestep: Optional[float] = timestep
        self.bias_factor: Optional[list[float]] = bias_factor
        self.iterations: Optional[int] = iterations
        self.temperature: Optional[float] = temperature
        self.system_name: Optional[str] = system_name
        self.calculator: Optional[str] = calculator
        self.time_units: Optional[str] = time_units
        self.dist_units: Optional[str] = dist_units
        self.energy_units: Optional[str] = energy_units
        self.height: Optional[list[float]] = height
        self.pace: Optional[list[float]] = pace
        self.sigma: Optional[list[float]] = sigma
        self.grid_min: Optional[list[str]] = grid_min
        self.grid_max: Optional[list[str]] = grid_max
        self.grid_bin: Optional[list[str]] = grid_bin
        self.solvent: Optional[str] = solvent
        self.kT: Optional[float] = kT
        self.properties: Optional[list[str]] = properties
        self.md_timestep: Optional[float] = md_timestep
        self.md_friction: Optional[float] = md_friction
        self.md_communication: Optional[str] = md_communication
        self.md_runsteps: Optional[int] = md_runsteps
        self.md_freq_out: Optional[int] = md_freq_out
        self.md_interval: Optional[int] = md_interval

    def set_write_defaults_if_needed(
        self,
    ):
        self.timestep = self.timestep or 0.005
        self.bias_factor = self.bias_factor or []
        self.iterations = self.iterations or 1024
        self.temperature = self.temperature or 300
        self.system_name = self.system_name or "generic_molecule"
        self.calculator = self.calculator or "GFN2-xTB"
        self.time_units = self.time_units or "1000 * units.fs"
        self.dist_units = self.dist_units or "A"
        self.energy_units = self.energy_units or "{units.mol/units.kJ}"
        self.height = self.height or []
        self.pace = self.pace or []
        self.sigma = self.sigma or []
        self.grid_min = self.grid_min or []
        self.grid_max = self.grid_max or []
        self.grid_bin = self.grid_bin or []
        self.solvent = self.solvent or "none"
        self.kT = self.kT or 0.025
        self.properties = self.properties or ["energy", "forces"]
        self.md_timestep = self.md_timestep or 1.0
        self.md_friction = self.md_friction or 0.01
        self.md_communication = self.md_communication or "world"
        self.md_runsteps = self.md_runsteps or 100000
        self.md_freq_out = self.md_freq_out or 10000
        self.md_interval = self.md_interval or self.md_runsteps / self.md_freq_out

    ## need some complex logic here to define MTD arguments etc.
    def build_mtd_setup_str(self):
        print("function to build mtd setup string")
        system_str = Template(
            textwrap.dedent(
                """
            [f"UNITS LENGTH=$dist_units TIME=XXXX ENERGY=$energy_units",
             "t1: TORSION ATOMS=6,4,9,2",
             "METAD ARG=t1 HEIGHT=0.25 PACE=100 " +
             "SIGMA=0.20 GRID_MIN=-pi GRID_MAX=pi" +
             " GRID_BIN=150 BIASFACTOR=5 FILE=HILLS"]

             """
            )
        )
        # subsitute template values into script
        script_text = system_str.substitute(
            # train_size=self.train_size,
        )

    # write file from a template
    def _write_file(self, path: Path, *args, **kwargs):
        self.set_write_defaults_if_needed()

        # set up template for polus script
        mtd_traj_script_template = Template(
            textwrap.dedent(
                """
            from ase import units
            from ase.io import read,write,Trajectory
            from xtb.ase.calculator import XTB
            from ase.md.langevin import Langevin
            from ichor.core.files.mtd.plumed_calculator import Plumed
            from ase.parallel import world

            timestep = $time_step
            ps = $time_units
            
            
            setup = $system_str

            # Define molecule
            mol_mtd = read(filename="$mol_xyz", format="xyz")

            # Define trajectory object
            traj = Trajectory(filename="$traj_path",atoms=mol_mtd, mode="w", properties=$properties)

            # Define calculator
            xtb_calc = XTB(method="$calculator",solvent="$solvent", electronic_temperature=$temperature, max_iterations=$iterations)
            
            # Attach Plumed calculator to atoms object
            mol_mtd.calc = Plumed(calc=xtb_calc,
                                input=setup,
                                timestep=timestep,
                                atoms=mol_mtd,
                                log="PLUMED.log",
                                restart = False,
                                kT=$kT)
            # Define dynamic object
            dyn = Langevin(atoms=mol_mtd, 
                          timestep=$md_timestep, 
                          temperature_K=$temperature,
                          friction=$md_friction/units.fs,
                          communicator = $md_communicator,
                          logfile = "$log_file_name")
            
            # Attach trajectory
            dyn.attach(traj.write, interval=$md_interval)

            # Run dynamic
            dyn.run($md_runsteps)
            traj.close()

            # Write trajectory
            traj_read = Trajectory(filename="$traj_path",mode="r",properties=$properties)
            write(filename="$mtd_out_file",format="xyz", images=traj_read, append=True)

            # Delete traj.write object file
            os.remove("$traj_path")

        """
            )
        )

        # subsitute template values into script
        script_text = mtd_traj_script_template.substitute(
            train_size=self.train_size,
        )

        return script_text
