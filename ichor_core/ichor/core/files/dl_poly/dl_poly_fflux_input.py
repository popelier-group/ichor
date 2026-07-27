from pathlib import Path
from typing import Optional, Union

from ichor.core.files.file import WriteFile


class DlPolyFFLUXInput(WriteFile):
    """Write out a ``FFLUX.in`` file. This file contains the FFLUX-specific settings
    for a DL_FFLUX calculation (the FFLUX modification of DL_POLY). Note that this is
    the *input* file for FFLUX and is different from the ``FFLUX`` file which FFLUX
    *writes out* (see :class:`ichor.core.files.dl_poly.DlPolyFFLUX`).

    :param path: The path to the FFLUX.in file, defaults to ``Path("FFLUX.in")``.
    :param title: The (optional) title written on the first line of the file.
    :param print_energy: Whether to write the IQA_ENERGY file, defaults to True.
    :param print_force: Whether to write the IQA_FORCES file, defaults to True.
    :param print_start: The timestep from which to start printing the FFLUX file,
        defaults to 0.
    :param print_every: How often (in timesteps) to print to the FFLUX file, defaults to 1.
    :param electrostatics: The electrostatics model to use, either ``"cluster"`` or
        ``"ewald"``. If ``None`` (default), no electrostatics directive is written. This
        should only be set when the models contain multipole moment data.
    :param electrostatics_level: The electrostatics multipole expansion level (L1-L5),
        defaults to 3. Only used when ``electrostatics`` is not ``None``.
    """

    _filetype = ""

    def __init__(
        self,
        path: Union[Path, str] = Path("FFLUX.in"),
        title: str = "Optional title",
        print_energy: bool = True,
        print_force: bool = True,
        print_start: int = 0,
        print_every: int = 1,
        electrostatics: Optional[str] = None,
        electrostatics_level: int = 3,
    ):

        super().__init__(path)

        self.title = title
        self.print_energy = print_energy
        self.print_force = print_force
        self.print_start = print_start
        self.print_every = print_every
        self.electrostatics = electrostatics
        self.electrostatics_level = electrostatics_level

    def _write_file(self, path: Path, *args, **kwargs):

        write_str = ""

        write_str += f"{self.title}\n"
        write_str += "\n"
        # Write IQA_ENERGY and IQA_FORCES files. Default: false
        if self.print_energy:
            write_str += "print energy\n"
        if self.print_force:
            write_str += "print force\n"
        write_str += "\n"
        # Specify start and frequency of printing the FFLUX file.
        write_str += f"print start {self.print_start}\n"
        write_str += f"print every {self.print_every}\n"
        # Electrostatics directive is only relevant when there is multipole moment data.
        if self.electrostatics is not None:
            write_str += "\n"
            write_str += f"{self.electrostatics} L{self.electrostatics_level}\n"

        return write_str
