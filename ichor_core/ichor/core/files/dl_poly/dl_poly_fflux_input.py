from pathlib import Path
from typing import Optional, Union

from ichor.core.files.file import WriteFile


class DlPolyFFLUXInput(WriteFile):
    """Write out a ``FFLUX.in`` file. This file contains the FFLUX-specific settings
    for a DL_FFLUX calculation (the FFLUX modification of DL_POLY). Note that this is
    the *input* file for FFLUX and is different from the ``FFLUX`` file which FFLUX
    *writes out* (see :class:`ichor.core.files.dl_poly.DlPolyFFLUX`).

    The full set of FFLUX directives is written out: the active ones are toggled on
    according to the arguments below, and the remaining options are written as comments
    (prefixed with ``#``) so that the user can uncomment and adjust them as needed.

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

        # a leading "#" comments a directive out; the active directives are toggled on
        # while the remaining options are written as comments for the user to adjust
        energy_prefix = "" if self.print_energy else "#"
        force_prefix = "" if self.print_force else "#"
        ewald_prefix = "" if self.electrostatics == "ewald" else "#"
        cluster_prefix = "" if self.electrostatics == "cluster" else "#"
        lvl = self.electrostatics_level

        write_str = ""

        write_str += f"{self.title}\n"
        write_str += "\n"
        write_str += "# Write IQA_ENERGY and IQA_FORCES files. Default: false\n"
        write_str += f"{energy_prefix}print energy\n"
        write_str += f"{force_prefix}print force\n"
        write_str += "\n"
        write_str += (
            "# Specify start and frequency of printing the FFLUX file. "
            "FFLUX file is always written.\n"
        )
        write_str += f"print start {self.print_start}\n"
        write_str += f"print every {self.print_every}\n"
        write_str += "\n"
        write_str += "# Enable delta learning\n"
        write_str += "#delta\n"
        write_str += "\n"
        # electrostatics directives are only meaningful with multipole moment data; the
        # relevant one is uncommented via its prefix, otherwise both stay commented
        write_str += "# Ewald electrostatics L1-L5\n"
        write_str += f"{ewald_prefix}ewald L{lvl}\n"
        write_str += "# Cluster electrostatics L1-L5\n"
        write_str += f"{cluster_prefix}cluster L{lvl}\n"
        write_str += "\n"
        write_str += "# Set electrostatics cutoff radius\n"
        write_str += "#cut dipole 8.0\n"
        write_str += "#cut quadrupole 8.0\n"
        write_str += "\n"
        write_str += "# Calculate forces numerically\n"
        write_str += "#numerical\n"
        write_str += (
            "# Specify the displacement in the numerical force calculation. "
            "Default: 0.0001\n"
        )
        write_str += "#numerical h 1.0e-6 # or just h 1.0e-6\n"
        write_str += (
            "# Numerical forces by forward difference instead of central difference. "
            "Not yet implemented\n"
        )
        write_str += "#numerical forward # or just forward\n"
        write_str += "\n"
        write_str += "# Write the DIPOLE file. Specify printing start and frequency\n"
        write_str += "#dipole\n"
        write_str += "#dipole print start 0\n"
        write_str += "#dipole print every 1\n"
        write_str += "\n"
        write_str += "# Electrostatic convergence test option\n"
        write_str += "#conv\n"

        return write_str
