from pathlib import Path
from typing import Optional, Union

from ichor.core.files.dl_poly.dl_poly_composition import MolecularComposition
from ichor.core.files.file import WriteFile
from ichor.core.files.xyz.trajectory import Trajectory


class DlPolyConfig(WriteFile):
    """Write out a DLPoly CONFIG file. The name of the file needs to be CONFIG,  so DL POLY knows to use it.

    :param system_name: the name of the chemical system. Ignored (in favour of the name of
        each species) when a ``composition`` is given.
    :param trajectory: a Trajectory instance containing the geometries that are going to be written to
        the CONFIG file. Each timestep in the trajectory is an Atoms instance.
    :param path: The path to the CONFIG file, defaults to Path('CONFIG')
    :param cell_size: The size of the box, float
    :param comment line: The very first line in the CONFIG file.
        Must be below 72 characters
    :param composition: The molecular composition of the box (see
        :class:`ichor.core.files.dl_poly.MolecularComposition`), used when the geometry holds
        many molecules - as a condensed phase box out of Packmol does. The atoms of each
        timestep are then written out molecule by molecule (in the order DL_POLY reads them
        into the molecular types declared in the FIELD file) and labelled with the name of
        their own species and their position *within their molecule*, so that DL_FFLUX finds
        the right model file for each of them. If ``None`` (default), the geometry is taken
        to be a single molecule and its atoms are labelled with ``system_name`` and their
        position in the timestep.

        .. note::
            ALL of the timesteps in the Trajectory will be written to one
            CONFIG file. Each timestep groups geometries which should be
            represented by a GP model. For example, if each timestep is
            only one molecule, then it means it is a monomer model and the
            labels of the atoms in the CONFIG will show that. If each timestep
            is two molecules, it means it is a dimer model, so then the
            labels in the CONFIG file will make sure that two molecules
            which should be represented by one GP model have the correct atom labeling
            in the CONFIG file.
    """

    # there is no suffix
    _filetype = ""

    def __init__(
        self,
        system_name: str,
        trajectory: Trajectory,
        path: Union[Path, str] = Path("CONFIG"),
        cell_size: float = 50.0,
        comment_line="Frame :         1\n",
        composition: Optional[MolecularComposition] = None,
    ):

        super().__init__(path)
        self.system_name = system_name
        self.trajectory = trajectory
        self.cell_size = float(cell_size)
        self.comment_line = comment_line
        self.composition = composition

    # TODO: implement reading for dlpoly config file
    # def _read_file(self):
    #     ...

    def _labelled_atoms(self, timestep):
        """Yields the atoms of one timestep in the order they are written out, each with the
        label DL_FFLUX matches against its model files.

        Without a composition the timestep is one molecule, so the atoms keep the order they
        are stored in and are labelled with their position in the timestep. With one, the
        atoms are grouped into their molecules and labelled with the name of their species
        and their position within their own molecule, so that every copy of a species reuses
        the same (single molecule's worth of) models.
        """

        if self.composition is None:
            for atom in timestep:
                yield atom, f"{self.system_name}_{atom.type}{atom.index}"
            return

        if self.composition.total_atoms != len(timestep):
            raise ValueError(
                f"The composition holds {self.composition.total_atoms} atoms "
                f"({self.composition}) but the geometry holds {len(timestep)}."
            )

        for species_index, atom_indices in self.composition.molecules:
            species = self.composition.species[species_index]
            for position, atom_index in enumerate(atom_indices):
                atom = timestep[atom_index]
                # the atoms of every molecule of a species have to line up with the
                # species' template, since that is what fixes which model belongs to which
                # atom. A molecule whose atoms are stored in a different order would
                # silently be given the wrong models, so say so instead.
                template_atom = species.atoms[position]
                if atom.type != template_atom.type:
                    raise ValueError(
                        f"A molecule of species '{species.system_name}' has a "
                        f"{atom.type} atom where the species holds a "
                        f"{template_atom.type} atom (atom {position + 1} of the "
                        "molecule). Every molecule of a species must list its atoms in "
                        "the same order."
                    )
                yield atom, f"{species.system_name}_{template_atom.name}"

    def _write_file(self, path: Path, vmd_compatible=False):

        write_str = ""

        write_str += self.comment_line
        # see dlpoly manual 4 for settings, VMD needs to have the third optional number
        # which is the total number of particles in the system
        # (the number of timesteps * the number of atoms in one timestep)
        if vmd_compatible:
            write_str += f"0  1  {len(self.trajectory) * len(self.trajectory[0])}\n"
        else:
            write_str += "0  1\n"  # PBC Solution to temporary problem
        write_str += f"{self.cell_size} 0.0 0.0\n"
        write_str += f"0.0 {self.cell_size} 0.0\n"
        write_str += f"0.0 0.0 {self.cell_size}\n"
        total_atoms_counter = 1

        if vmd_compatible:
            for timestep in self.trajectory:
                for atom in timestep:
                    write_str += f"{atom.type}  {total_atoms_counter}\n"
                    write_str += f"{atom.x}\t\t{atom.y}\t\t{atom.z}\n"
                    total_atoms_counter += 1
        # if CONFIG is going to be used in FFLUX, then add the index of the atoms.
        # This indicates the model file that is going to be used for that atom.
        else:
            for timestep in self.trajectory:
                for atom, label in self._labelled_atoms(timestep):
                    write_str += f"{atom.type}  {total_atoms_counter}  {label}\n"
                    write_str += f"{atom.x}\t\t{atom.y}\t\t{atom.z}\n"
                    total_atoms_counter += 1

        return write_str
