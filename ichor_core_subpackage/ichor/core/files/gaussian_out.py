from pathlib import Path
from typing import Union, List, Dict

from ichor.core.atoms import Atom, Atoms
from ichor.core.common.functools import classproperty
from ichor.core.common.str import split_by
from ichor.core.files.file import FileContents, ReadFile, File
from ichor.core.files.file_data import HasAtoms, HasProperties
from ichor.core.units import AtomicDistance

class GaussianOut(HasAtoms, HasProperties, ReadFile):
    """Wraps around a .wfn file that is the output of Gaussian. The .wfn file is
    an output file, so it does not have a write method.

    :param path: Path object or string to the .wfn file
    :param atoms: an Atoms instance which is read in from the top of the .wfn file.
        Note that the units of the .wfn file are in Bohr.
    :param method: The method (eg. B3LYP) which was used in the Gaussian calculation
        that created the .wfn file. The method is not initially written to the .wfn
        file by Gaussian, but it is necessary to add it to the .wfn file because
        AIMAll does not automatically determine the method itself, so it can lead
        to wrong IQA/multipole moments results. To make sure AIMAll results are correct,
        the method is a required argument.
    :param mol_orbitals: The number of molecular orbitals to be read in from the .wfn file.
    :param primitives: The number of primitives to be read in from the .wfn file.
    :param nuclei: The number of nuclei in the system to be read in from the .wfn file.
    :param energy: The molecular energy read in from the bottom of the .wfn file
    :param virial: The virial read in from the bottom of the .wfn file
    .. note::
        Since the wfn file is written out by Gaussian, we do not really have to modify it when writing out except
        we need to add the method used, so that AIMALL can use the correct method. Otherwise AIMALL assumes Hartree-Fock
        was used, which might be wrong.
    """

    def __init__(
        self,
        path: Union[Path, str],
        forces = None,
        atoms = None,
    ):
        File.__init__(self, path)
        self.forces = forces or FileContents
        self.atoms = atoms or FileContents

    def _read_file(self):
        """Parse through a .wfn file to look for the relevant information. This is automatically called if an attribute is being accessed, but the
        FileState of the file is FileState.Unread"""

        atoms = Atoms()
        with open(self.path, "r") as f:
            
            for l in f:
                if " Charge =  0 Multiplicity = 1" in l:
                    break
                
            line = next(f)
            
            while line.strip():
                line = line.split()
                atom_type = line[0]
                x = float(line[1])
                y = float(line[2])
                z = float(line[3])
                atoms.add(
                    Atom(
                        atom_type,
                        x,
                        y,
                        z,
                        units=AtomicDistance.Angstroms,
                    )
                )
                line = next(f)
            
            contains_forces = False
            forces = {}
            
            for l in f:
                if "Forces (Hartrees/Bohr)" in l:
                    contains_forces = True
                    break
            
            if contains_forces:
                # this is the ---------------- line
                line = next(f)
                
                for atom_name in atoms.names:
                    line = next(f).split()
                    forces[atom_name] = (float(line[3]), float(line[4]), float(line[5]))

        self.forces = self.forces or forces
        self.atoms = self.atoms or atoms

    @classproperty
    def filetype(cls) -> str:
        """Returns the file extension of a WFN file"""
        return ".wfn"

    @classproperty
    def property_names(self) -> List[str]:
        return ["forces"]

    @property
    def properties(self) -> Dict[str, float]:
        return {"forces": self.forces}