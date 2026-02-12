from os.path import exists

import numpy as np

from ase.calculators.calculator import Calculator, all_changes
from ase.io.trajectory import Trajectory
from ase.parallel import broadcast, world
from ase.units import fs, kJ, mol, nm


def restart_from_trajectory(prev_traj, *args, prev_steps=None, atoms=None, **kwargs):
    """This function helps the user to restart a plumed simulation
    from a trajectory file.

    Parameters
    ----------
    prev_traj : Trajectory object
        previous simulated trajectory

    prev_steps : int. Default steps in prev_traj.
        number of previous steps

    others :
       Same parameters of :mod:`~ase.calculators.plumed` calculator

    Returns
    -------
    Plumed calculator


    .. note:: prev_steps is crucial when trajectory does not contain
        all the previous steps.
    """
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
        """
        Plumed calculator is used for simulations of enhanced sampling methods
        with the open-source code PLUMED (plumed.org).

        [1] The PLUMED consortium, Nat. Methods 16, 670 (2019)
        [2] Tribello, Bonomi, Branduardi, Camilloni, and Bussi,
        Comput. Phys. Commun. 185, 604 (2014)

        Parameters
        ----------
        calc: Calculator object
            It  computes the unbiased forces

        input: List of strings
            It contains the setup of plumed actions

        timestep: float
            Time step of the simulated dynamics

        atoms: Atoms
            Atoms object to be attached

        kT: float. Default 1.
            Value of the thermal energy in eV units. It is important for
            some methods of plumed like Well-Tempered Metadynamics.

        log: string
            Log file of the plumed calculations

        restart: boolean. Default False
            True if the simulation is restarted.

        use_charge: boolean. Default False
            True if you use some collective variable which needs charges. If
            use_charges is True and update_charge is False, you have to define
            initial charges and then this charge will be used during all
            simulation.

        update_charge: boolean. Default False
            True if you want the charges to be updated each time step. This
            will fail in case that calc does not have 'charges' in its
            properties.


        .. note:: For this case, the calculator is defined strictly with the
            object atoms inside. This is necessary for initializing the
            Plumed object. For conserving ASE convention, it can be initialized
            as atoms.calc = (..., atoms=atoms, ...)


        .. note:: In order to guarantee a proper restart, the user has to fix
            momenta, positions and Plumed.istep, where the positions and
            momenta corresponds to the last configuration in the previous
            simulation, while Plumed.istep is the number of timesteps
            performed previously. This can be done using
            ase.calculators.plumed.restart_from_trajectory.
        """

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

            """ Units setup
            warning: inputs and outputs of plumed will still be in
            plumed units.

            The change of Plumed units to ASE units is:
            kjoule/mol to eV
            nm to Angstrom
            ps to ASE time units
            ASE and plumed - charge unit is in e units
            ASE and plumed - mass unit is in a.m.u units """

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
        """This function computes what is required in
        plumed input for some trajectory.

        The outputs are saved in the typical files of
        plumed such as COLVAR, HILLS"""
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
