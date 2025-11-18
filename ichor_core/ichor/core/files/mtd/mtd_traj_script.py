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

        self.hills_file = self.hills_file or self.input_xyz_path.with_suffix(".HILLS")
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
            grid_bin_line = f'\t" GRID_BIN={self.grid_bin[0]} BIASFACTOR={self.bias_factor} FILE={self.hills_file}"]\n'
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
            from os.path import exists
            import numpy as np
            from ase import units
            from ase.units import fs, kJ, mol, nm
            from ase.calculators.calculator import Calculator, all_changes
            from ase.io import read,write,Trajectory
            from xtb.ase.calculator import XTB
            from ase.md.langevin import Langevin
            from ase.parallel import broadcast, world

            def restart_from_trajectory(prev_traj, *args, prev_steps=None, atoms=None, **kwargs):
                atoms.calc = Plumed(*args, atoms=atoms, restart=True, **kwargs)
    
                with Trajectory(prev_traj) as traj:
                    if prev_steps is None:
                        atoms.calc.istep = len(traj) - 1
                    else:
                        atoms.calc.istep = prev_steps
                    atoms.set_positions(traj[-1].get_positions())
                    atoms.set_momenta(traj[-1].get_momenta())
                return atoms.calc


            class Plumed(Calculator):
                implemented_properties = ["energy", "forces"]

                def __init__(
                    self,
                    calc,
                    input,
                    timestep,
                    atoms=None,
                    kT=1.0,
                    log="",
                    restart=False,
                    use_charge=False,
                    update_charge=False,
                ):
                    from plumed import Plumed as pl

                    if atoms is None:
                        raise TypeError(
                            "plumed calculator has to be defined with the \
                                         object atoms inside."
                        )

                    self.istep = 0
                    Calculator.__init__(self, atoms=atoms)

                    self.input = input
                    self.calc = calc
                    self.use_charge = use_charge
                    self.update_charge = update_charge

                    if world.rank == 0:
                        natoms = len(atoms.get_positions())
                        self.plumed = pl()
                        ps = 1000 * fs
                        self.plumed.cmd("setMDEnergyUnits", mol / kJ)
                        self.plumed.cmd("setMDLengthUnits", 1 / nm)
                        self.plumed.cmd("setMDTimeUnits", 1 / ps)
                        self.plumed.cmd("setMDChargeUnits", 1.0)
                        self.plumed.cmd("setMDMassUnits", 1.0)

                        self.plumed.cmd("setNatoms", natoms)
                        self.plumed.cmd("setMDEngine", "ASE")
                        self.plumed.cmd("setLogFile", log)
                        self.plumed.cmd("setTimestep", float(timestep))
                        self.plumed.cmd("setRestart", restart)
                        self.plumed.cmd("setKbT", float(kT))
                        self.plumed.cmd("init")
                        for line in input:
                            self.plumed.cmd("readInputLine", line)
                    self.atoms = atoms

                def _get_name(self):
                    return f"{self.calc.name}+Plumed"

                def calculate(
                    self, atoms=None, properties=["energy", "forces"], system_changes=all_changes
                ):
                    Calculator.calculate(self, atoms, properties, system_changes)

                    comp = self.compute_energy_and_forces(self.atoms.get_positions(), self.istep)
                    energy, forces = comp
                    self.istep += 1
                    self.results["energy"], self.results["forces"] = energy, forces

                def compute_energy_and_forces(self, pos, istep):
                    unbiased_energy = self.calc.get_potential_energy(self.atoms)
                    unbiased_forces = self.calc.get_forces(self.atoms)

                    if world.rank == 0:
                        ener_forc = self.compute_bias(pos, istep, unbiased_energy)
                    else:
                        ener_forc = None
                    energy_bias, forces_bias = broadcast(ener_forc)
                    energy = unbiased_energy + energy_bias
                    forces = unbiased_forces + forces_bias
                    return energy, forces

                def compute_bias(self, pos, istep, unbiased_energy):
                    self.plumed.cmd("setStep", istep)

                    if self.use_charge:
                        if "charges" in self.calc.implemented_properties and self.update_charge:
                            charges = self.calc.get_charges(atoms=self.atoms.copy())

                        elif self.atoms.has("initial_charges") and not self.update_charge:
                            charges = self.atoms.get_initial_charges()

                        else:
                            assert not self.update_charge, "Charges cannot be updated"
                            assert self.update_charge, "Not initial charges in Atoms"

                        self.plumed.cmd("setCharges", charges)

                    # Box for functions with PBC in plumed
                    if self.atoms.cell:
                        cell = np.asarray(self.atoms.get_cell())
                        self.plumed.cmd("setBox", cell)

                    self.plumed.cmd("setPositions", pos)
                    self.plumed.cmd("setEnergy", unbiased_energy)
                    self.plumed.cmd("setMasses", self.atoms.get_masses())
                    forces_bias = np.zeros((self.atoms.get_positions()).shape)
                    self.plumed.cmd("setForces", forces_bias)
                    virial = np.zeros((3, 3))
                    self.plumed.cmd("setVirial", virial)
                    self.plumed.cmd("prepareCalc")
                    self.plumed.cmd("performCalc")
                    energy_bias = np.zeros((1,))
                    self.plumed.cmd("getBias", energy_bias)
                    return [energy_bias, forces_bias]

                def write_plumed_files(self, images):
                    for i, image in enumerate(images):
                        pos = image.get_positions()
                        self.compute_energy_and_forces(pos, i)
                    return self.read_plumed_files()

                def read_plumed_files(self, file_name=None):
                    read_files = {}
                    if file_name is not None:
                        read_files[file_name] = np.loadtxt(file_name, unpack=True)
                    else:
                        for line in self.input:
                            if line.find("FILE") != -1:
                                ini = line.find("FILE")
                                end = line.find(" ", ini)
                                if end == -1:
                                    file_name = line[ini + 5 :]
                                else:
                                    file_name = line[ini + 5 : end]
                                read_files[file_name] = np.loadtxt(file_name, unpack=True)

                        if len(read_files) == 0:
                            if exists("COLVAR"):
                                read_files["COLVAR"] = np.loadtxt("COLVAR", unpack=True)
                            if exists("HILLS"):
                                read_files["HILLS"] = np.loadtxt("HILLS", unpack=True)
                    assert len(read_files) != 0, "There are not files for reading"
                    return read_files

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    self.plumed.finalize()

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
                self.system_name + "_mtd_out.xyz"
            ),
        )

        return script_text
