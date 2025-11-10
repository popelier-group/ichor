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
        bias_factor: Optional[float] = None,
        hills_file: Optional[str] = None,
        iterations: Optional[int] = None,
        temperature: Optional[float] = None,
        system_name: Optional[str] = None,
        calculator: Optional[str] = None,
        time_units: Optional[str] = None,
        dist_units: Optional[str] = None,
        energy_units: Optional[str] = None,
        height: Optional[float] = None,
        pace: Optional[float] = None,
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
        self.bias_factor: Optional[float] = bias_factor
        self.hills_file: Optional[str] = hills_file
        self.iterations: Optional[int] = iterations
        self.temperature: Optional[float] = temperature
        self.system_name: Optional[str] = system_name
        self.calculator: Optional[str] = calculator
        self.time_units: Optional[str] = time_units
        self.dist_units: Optional[str] = dist_units
        self.energy_units: Optional[str] = energy_units
        self.height: Optional[float] = height
        self.pace: Optional[float] = pace
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
        sigma_list = []
        grid_min_list = []
        grid_max_list = []
        grid_bin_list = []
        # build lists of defaults for multi cv
        for i in range(len(self.collective_variables)):
            sigma_list.append(0.20)
            grid_min_list.append("-pi")
            grid_max_list.append("pi")
            grid_bin_list.append(200)

        self.hills_file = self.hills_file or "HILLS"
        self.sigma = self.sigma or sigma_list
        self.grid_min = self.grid_min or grid_min_list
        self.grid_max = self.grid_max or grid_max_list
        self.grid_bin = self.grid_bin or grid_bin_list
        self.timestep = self.timestep or 0.005
        self.bias_factor = self.bias_factor or 5
        self.iterations = self.iterations or 1024
        self.temperature = self.temperature or 300
        self.system_name = self.system_name or "generic_molecule"
        self.calculator = self.calculator or '"GFN2-xTB"'
        self.time_units = self.time_units or "1000 * units.fs"
        self.dist_units = self.dist_units or "A"
        self.energy_units = self.energy_units or "{units.mol/units.kJ}"
        self.height = self.height or 0.25
        self.pace = self.pace or 200
        self.solvent = self.solvent or "none"
        self.kT = self.kT or 0.025
        self.properties = self.properties or ["energy", "forces"]
        self.md_timestep = self.md_timestep or 1.0
        self.md_friction = self.md_friction or 0.01
        self.md_communication = self.md_communication or "world"
        self.md_runsteps = self.md_runsteps or 100000
        self.md_freq_out = self.md_freq_out or 10000
        self.md_interval = self.md_interval or int(self.md_runsteps / self.md_freq_out)

    def build_cv_str(self, cv, num, group):
        print("MAKE SINGLE CV STRING")
        if group == "":
            cv_to_str = ",".join(str(i) for i in cv)
        else:
            cv_to_str = group
        if len(cv) == 2:
            cv_str = f'\t"m{num}: DISTANCE ATOMS={cv_to_str}",\n'
        elif len(cv) == 3:
            cv_str = f'\t"m{num}: ANGLE ATOMS={cv_to_str}",\n'
        elif len(cv) == 4:
            cv_str = f'\t"m{num}: TORSION ATOMS={cv_to_str}",\n'
        return cv_str

    def build_group_str(self, cv, num):
        print("MAKE SINGLE GROUP STRING")
        cv_to_str = ",".join(str(i) for i in cv)
        group_str = f'\t"GROUP ATOMS={cv_to_str} LABEL=g{num}",\n'
        return group_str

    ## need some complex logic here to define MTD arguments etc.
    def build_mtd_setup_str(self):

        print("function to build mtd setup string")
        header_line = f'[f"UNITS LENGTH={self.dist_units} TIME={{1/ps}} ENERGY={self.energy_units}",\n'
        if len(self.collective_variables) == 1:
            print("BUILDING SETUP STRING FOR SINGLE VARIABLE")
            cv_line = self.build_cv_str(self.collective_variables[0], 1, "")
            metad_line = f'\t"METAD ARG=m1 HEIGHT={self.height} PACE={self.pace} " +\n'
            sigma_line = f'\t"SIGMA={self.sigma[0]} GRID_MIN={self.grid_min[0]} GRID_MAX={self.grid_max[0]}" +\n'
            grid_bin_line = f'\t" GRID_BIN={self.grid_bin[0]} BIASFACTOR={self.bias_factor} FILE={self.hills_files[0]}"]\n'
            setup_str = header_line + cv_line + metad_line + sigma_line + grid_bin_line
            return setup_str
        else:
            print("BUILDING SETUP STRING FOR MULTIPLE VARIABLES")
            group_line = ""
            cv_line = ""
            arg_list = []
            for i in range(len(self.collective_variables)):
                group_line += self.build_group_str(self.collective_variables[i], i + 1)
                cv_line += self.build_cv_str(
                    self.collective_variables[i], i + 1, f"g{i+1}"
                )
                arg_list.append(f"m{i+1}")
            arg_str = ",".join(str(i) for i in arg_list)
            sigma_str = ",".join(str(i) for i in self.sigma)
            grid_min_str = ",".join(str(i) for i in self.grid_min)
            grid_max_str = ",".join(str(i) for i in self.grid_max)
            grid_bin_str = ",".join(str(i) for i in self.grid_bin)
            pbmetad_line = f'\t"PBMETAD ARG={arg_str} SIGMA={sigma_str} PACE={self.pace} HEIGHT={self.height} " +\n'
            grid_bin_line = f'\t"GRID_MIN={grid_min_str} GRID_MAX={grid_max_str} GRID_BIN={grid_bin_str} "+\n'
            hill_file_str = self.hills_file
            bias_factor_line = (
                f'\t"BIASFACTOR={self.bias_factor} FILE={hill_file_str}"]\n'
            )
            setup_str = (
                header_line
                + group_line
                + cv_line
                + pbmetad_line
                + grid_bin_line
                + bias_factor_line
            )
            return setup_str

    # write file from a template
    def _write_file(self, path: Path, *args, **kwargs):
        self.set_write_defaults_if_needed()
        system_str_built = self.build_mtd_setup_str()

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
                          timestep=$md_timestep*units.fs, 
                          temperature_K=$temperature,
                          friction=$md_friction/units.fs,
                          #communicator = $md_communicator,
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
            time_step=self.timestep,
            time_units=self.time_units,
            system_str=system_str_built,
            mol_xyz=self.input_xyz_path,
            traj_path=self.input_xyz_path.with_suffix(".traj"),
            properties=self.properties,
            calculator=self.calculator,
            solvent=self.solvent,
            temperature=self.temperature,
            iterations=self.iterations,
            kT=self.kT,
            md_timestep=self.md_timestep,
            md_friction=self.md_friction,
            md_communicator=self.md_communication,
            log_file_name=self.input_xyz_path.with_suffix(".log"),
            md_interval=self.md_interval,
            md_runsteps=self.md_runsteps,
            mtd_out_file=self.input_xyz_path.with_name(
                self.system_name + "mtd_out.xyz"
            ),
        )

        return script_text
