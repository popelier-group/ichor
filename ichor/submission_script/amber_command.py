from pathlib import Path
from typing import List, Optional

from ichor.common.functools import classproperty
from ichor.modules import AmberModules, Modules
from ichor.submission_script.command_line import CommandLine
from ichor.submission_script.ichor_command import ICHORCommand


class AmberCommand(CommandLine):
    """
    todo: write docs
    """

    def __init__(
        self,
        mol2_file: Path,
        mdin_file: Path,
    ):
        self.mol2_file = mol2_file
        self.mdin_file = mdin_file

    @classproperty
    def group(self) -> bool:
        return False

    @property
    def data(self) -> List[str]:
        """Return a list of the absolute paths of the Gaussian input file (.gjf) and the output file (.gau)"""
        return [str(self.mol2_file.absolute()), str(self.mdin_file.absolute())]

    @classproperty
    def modules(self) -> Modules:
        """Returns the modules that need to be loaded in order for Gaussian to work on a specific machine"""
        return AmberModules

    @classproperty
    def command(self) -> str:
        if self.ncores == 1:
            return "sander"
        else:
            return f"mpirun -n {self.ncores} sander.MPI"

    @classproperty
    def ncores(self) -> int:
        """Returns the number of cores that Amber should use for the job."""
        from ichor.globals import GLOBALS

        return GLOBALS.AMBER_NCORES

    def repr(self, variables: List[str]) -> str:
        """
        Returns a strings which is then written out to the final submission script file.
        If the outputs of the job need to be checked (by default self.rerun is set to True, so job outputs are checked),
        then the corresponsing strings are appended to the initial commands string.

        The length of `variables` is defined by the length of `self.data`
        """
        from ichor.globals import GLOBALS

        mol2_file = self.mol2_file.absolute()
        cmd = ""
        cmd += f"pushd {mol2_file.parent}\n"
        # run antechanmber to modify mol2 file for use in amber
        cmd += f"antechamber -i {mol2_file} -o {mol2_file} -fi mol2 -fo mol2 -c bcc -pf yes -nc -2 -at gaff2 -j 5 -rn {GLOBALS.SYSTEM_NAME.lower()}\n"
        # run parmchk to generate frcmod file
        frcmod_file = mol2_file.with_suffix(".frcmod")
        cmd += f"parmchk2 -i {mol2_file} -f mol2 -o {frcmod_file} -s 2\n"
        # run tleap to generate prmtop and inpcrd
        tleap_script = mol2_file.with_suffix(".tleap")
        prmtop_file = mol2_file.with_suffix(".prmtop")
        inpcrd_file = mol2_file.with_suffix(".inpcrd")
        with open(tleap_script, "w") as f:
            f.write("source leaprc.protein.ff14SB\n")
            f.write("source leaprc.gaff2\n")
            f.write(f"mol = loadmol2 {mol2_file}\n")
            f.write(f"loadamberparams {frcmod_file}\n")
            f.write(f"saveamberparm mol {prmtop_file} {inpcrd_file}\n")
            f.write(f"quit")
        cmd += f"tleap -f {tleap_script}\n"
        # run amber
        cmd += f"{AmberCommand.command} -O -i {self.mdin_file.absolute()} -o md.out -p {prmtop_file} -c {inpcrd_file} -inf md.info\n"

        cmd += "popd\n"

        mdcrd = (self.mol2_file.parent / "mdcrd").absolute()
        xyz = (
            f"{GLOBALS.SYSTEM_NAME}-amber-{int(GLOBALS.AMBER_TEMPERATURE)}.xyz"
        )
        ichor_command = ICHORCommand(
            func="mdcrd_to_xyz", func_args=[mdcrd, prmtop_file, xyz]
        )
        cmd += f"{ichor_command.repr(variables)}\n"
        ichor_command = ICHORCommand(
            func="set_points_location", func_args=[xyz]
        )
        cmd += f"{ichor_command.repr(variables)}\n"
        return cmd
