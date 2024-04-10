from pathlib import Path
from typing import List, NamedTuple, Optional, Union

from ichor.core.atoms import Atom, Atoms
from ichor.core.common.constants import GAUSSIAN_METHODS

# from enum import Enum
from ichor.core.common.types.enum import Enum
from ichor.core.files.file import FileContents, ReadFile, WriteFile
from ichor.core.files.file_data import HasAtoms


class PrintLevel(Enum):
    Normal = "n"
    Verbose = "p"
    Terse = "t"


class RouteCard(NamedTuple):
    print_level: PrintLevel
    method: str
    basis_set: str
    keywords: List[str]


class GJF(ReadFile, WriteFile, HasAtoms):
    """

    Wraps around a .gjf file that is used as input to Gaussian.
    See https://gaussian.com/input/ for details.
    Below is the usual gjf file structure:

    .. code-block:: text

        %nproc
        %mem
        # <job_type> <method>/<basis-set> <keywords>

        Title

        0 1
        <atom-name> <todo: add -1 for freeze> <x> <y> <z>
        ...

        extra_details_str (containing basis sets for individual atoms, what to freeze, etc.)

        <wfn-name>
        blank line
        blank line
        blank line
        ...

    :param path: A string or Path to the .gjf file. If a path is not give,
        then there is no file to be read, so the user has to write the file contents. If
        no contents/options are written by user, they are written as the default values in the
        ``write`` method.
    :param title: A string to be written between the link0 options and the keywords.
        It can contain any information.
    :param job_type: The job type, an energy, optimization, or frequency
    :param keywords: A list of keywords to be added to the Gaussian keywords line
    :param method: The method to be used by Gaussian (e.g. B3LYP)
    :param basis_set: The basis set to be used by Gaussian (e.g. 6-31+g(d,p))
    :param charge: The charge to be used by Gaussian for the system
    :param multiplicity: The multiplicity to be used by Gaussian for the system.
    :param atoms: An Atoms instance containing a geometry to be written in the .gjf file.
        This is either read in (if an existing gjf path is given) or
        an error is thrown when attempting to write the gjf file (because no gjf file or `Atoms` instance was given)

    :param extra_calculation_details: A list of strings to be added to the bottom of the gjf file
        (after atoms section containing atom names and coordinates).
        This is done in order to handle different basis sets
        for individual atoms, modredundant settings, and other settings that Gaussian handles.

    .. note::

        It is up to the user to handle write the `extra_calculation_details` settings. ICHOR
        does NOT do checks to see if these additional settings are going to be read in correctly
        in Gaussian.

    """

    _filetype = ".gjf"

    def __init__(
        self,
        path: Union[Path, str],
        link0: Optional[List[str]] = None,
        print_level: PrintLevel = None,
        method: Optional[str] = None,
        basis_set: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        title: Optional[str] = None,
        charge: Optional[int] = None,
        spin_multiplicity: Optional[int] = None,
        atoms: Optional[Atoms] = None,
        output_chk: bool = False,
    ):
        super().__init__(path)

        self.link0: List[str] = link0 or FileContents

        self.print_level = print_level or FileContents
        self.method: str = method or FileContents
        self.basis_set: str = basis_set or FileContents
        self.keywords: List[str] = keywords or FileContents
        self.title = title or FileContents

        self.charge: int = charge or FileContents
        self.spin_multiplicity: int = spin_multiplicity or FileContents
        self.atoms = atoms or FileContents

        self._output_chk: bool = output_chk

    def _find_in_link(self, val: str) -> Optional[int]:
        return next(
            (i for i, l in enumerate(self.link0) if val.lower() in l.lower()),
            None,
        )

    def set_nproc(self, nproc: int):
        """
        Sets the number of processor cores for Gaussian

        :param nproc: An integer which is the number of cores.

        .. note::

            No checks are done for CPU core count.

        """
        nproc = f"nproc={nproc}"
        n = self._find_in_link("nproc")
        if n is None:
            self.link0.append(nproc)
        else:
            self.link0[n] = nproc

    def set_mem(self, mem: str):
        """
        Sets memory for Gaussian job

        :param mem: string to set as memory

        .. note::

            This is not checked internally.

        """
        mem = f"mem={mem}"
        n = self._find_in_link("mem")
        if n is None:
            self.link0.append(mem)
        else:
            self.link0[n] = mem

    def add_keyword(self, keyword: str):
        """Add a keyword to the Gaussian input keywords

        :param keywords: A string to add as a keyword

        .. note::

            The keyword is not checked internally.

        """

        if keyword not in self.keywords:
            self.keywords.append(keyword)

    def add_keywords(self, keywords: List[str]):
        """Add a list of keywords to the Gaussian input keywords

        :param keywords: A list of keywords

        .. note::

            The keywords are not checked internally.

        """
        for keyword in keywords:
            self.add_keyword(keyword)

    def output_wfn(self):
        """Helper method to add 'output=wfn' to the GJF keyword list"""
        self.add_keyword("output=wfn")

    @classmethod
    def parse_route_card(cls, route_card: str) -> RouteCard:
        method = None
        basis_set = None
        keywords = []
        # default the print level to verbose
        print_level = PrintLevel.Verbose

        route_card = route_card.replace("#", "")

        for keyword in route_card.split():
            if r"/" in keyword:
                method, basis_set = keyword.split(r"/")
            elif keyword.lower() in PrintLevel.values:
                print_level = PrintLevel(keyword.lower())
            else:
                keywords.append(keyword)
        return RouteCard(print_level, method, basis_set, keywords)

    def _initialise_contents(self):
        self.link0 = self.link0 or []
        self.method = self.method or ""
        self.basis_set = self.basis_set or ""
        self.keywords = self.keywords or []
        self.title = self.title or ""
        self.charge = self.charge or 0
        self.spin_multiplicity = self.spin_multiplicity or 0
        self.atoms = self.atoms or Atoms()

    def _read_file(self):
        with open(self.path, "r") as f:
            line = next(f)
            link0 = []

            while line.startswith(r"%"):
                link0.append(line.strip().replace("%", ""))
                line = next(f)

            route_lines = []
            # last loop line is set to a blank line (because a blank line terminates route section)
            while line.strip():
                route_lines.append(line.strip())
                line = next(f)
            route = " ".join(route_lines)

            # the comment line can be a blank line
            title = next(f).strip()
            # another blank line follows before moving to system definitions
            line = next(f)

            charge, spin_multiplicity = map(int, next(f).split())

            line = next(f)
            atoms = Atoms()
            while line.strip():
                atoms.append(Atom(*line.split()))
                try:
                    line = next(f)
                except StopIteration:
                    break

        self.link0 = self.link0 or link0
        route_card = self.parse_route_card(route)
        self.print_level = self.print_level or route_card.print_level
        self.method = self.method or route_card.method
        self.basis_set = self.basis_set or route_card.basis_set
        self.title = self.title or title
        self.keywords = self.keywords or route_card.keywords
        self.charge = self.charge or charge
        self.spin_multiplicity = self.spin_multiplicity or spin_multiplicity
        self.atoms = self.atoms or atoms

    def _set_write_defaults_if_needed(self):
        """Set default values for attributes if bool(self.attribute) evaluates to False.
        So if an attribute is still FileContents, an empty string, an empty list, etc.,
        then default values will be used."""

        self.link0 = self.link0 or []
        if self._output_chk and any("chk" in l0 for l0 in self.link0):
            self.link0.append(f"chk={self.path.with_suffix('.chk')}")

        self.print_level = self.print_level or PrintLevel.Verbose
        self.method = self.method or "b3lyp"
        self.basis_set = self.basis_set or "6-31+g(d,p)"
        self.keywords = self.keywords or [
            "nosymm",
            "output=wfn",
            "force",
            "geom=notest",
            "IOp(1/33=2)",  # verbosity level 2, prints out B matrix, G matrix and G inverse to output file
        ]

        self.title = self.title or str(self.path.stem)

        self.charge = self.charge or 0
        self.spin_multiplicity = self.spin_multiplicity or 1

    def _check_values_before_writing(self):
        """Basic checks done prior to writing file.

        .. note:: Not everything written to file can be checked for, so
        there is still the need for a user to check out what is being written.
        """

        if self.method.upper() not in GAUSSIAN_METHODS:
            raise ValueError(f"{self.method} is not available in Gaussian.")
        if self.spin_multiplicity < 1:
            raise ValueError(f"Spin multiplicity cannot be {self.spin_multiplicity}.")
        if len(self.atoms) == 0:
            raise ValueError("There are no atoms to write to gjf file.")

    def _write_file(self, path: Path, *args, **kwargs):
        fmtstr = "12.8f"

        write_str = ""

        for link0 in self.link0:
            write_str += f"%{link0}\n"
        write_str += f"#{self.print_level.value} {self.method}/{self.basis_set} {' '.join(self.keywords)}\n"
        write_str += "\n"
        write_str += f"{self.title}\n"
        write_str += "\n"
        write_str += f"{self.charge}   {self.spin_multiplicity}\n"
        for atom in self.atoms:
            write_str += (
                f"{atom.type} {atom.x:{fmtstr}} {atom.y:{fmtstr}} {atom.z:{fmtstr}}\n"
            )
        if "output=wfn" in self.keywords:
            write_str += f"\n{self.path.with_suffix('.wfn')}"
        # add newline character because Gaussian otherwise crashes
        # if requesting using other keywords but not output=wfn
        else:
            write_str += "\n"

        return write_str
