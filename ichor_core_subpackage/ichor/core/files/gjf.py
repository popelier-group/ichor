from pathlib import Path
from typing import List, Optional, Union, NamedTuple

from ichor.core.atoms import Atom, Atoms
from ichor.core.common.functools import classproperty
from ichor.core.files.file import FileContents, File, ReadFile, WriteFile
from ichor.core.files.file_data import HasAtoms

# from enum import Enum
from ichor.core.common.types.enum import Enum


class PrintLevel(Enum):
    Normal = "n"
    Verbose = "p"
    Terse = "t"


class RouteCard(NamedTuple):
    print_level: PrintLevel
    method: str
    basis_set: str
    keywords: List[str]


class GJF(ReadFile, WriteFile, File, HasAtoms):
    """
    https://gaussian.com/input/

    Wraps around a .gjf file that is used as input to Gaussian. Below is the usual gjf file structure:

        ----------------------------------------------------------
        %nproc
        %mem
        # <job_type> <method>/<basis-set> <keywords>

        Title

        0 1
        <atom-name> <todo: add -1 for freeze> <x> <y> <z>
        ...

        extra_details_str (containing basis sets for individual atoms, what to freeze, etc.)

        <wfn-name>
        -----------------------------------------------------------

    :param path: A string or Path to the .gjf file. If a path is not give,
        then there is no file to be read, so the user has to write the file contents. If
        no contents/options are written by user, they are written as the default values in the
        `write` method.
    :param comment_line: A string to be written between the link0 options and the keywords.
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

    # todo: fix below docstring
    :param extra_details_str: A string (can contain multiple lines separated with new line character).
        These will be added to the bottom of the gjf file. This is done in order to handle different basis sets
        for individual atoms, modredundant settings, and other settings that Gaussian handles.

    .. note::
        It is up to the user to handle write the `extra_details_str` settings. ICHOR
        does NOT do checks to see if these additional settings are going to be read in correctly
        in Gaussian.
    """

    def __init__(
        self,
        path: Union[Path, str],
        link0: Optional[List[str]] = None,
        print_level: PrintLevel = None,
        method: Optional[str] = None,
        basis_set: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        comment_line: Optional[str] = None,
        charge: Optional[int] = None,
        spin_multiplicity: Optional[int] = None,
        atoms: Optional[Atoms] = None,
        output_chk: bool = False,
    ):
        File.__init__(self, path)
        HasAtoms.__init__(self, atoms)

        self.link0: List[str] = link0 or FileContents

        self.print_level = print_level or FileContents
        self.method: str = method or FileContents
        self.basis_set: str = basis_set or FileContents
        self.keywords: List[str] = keywords or FileContents
        self.comment_line = comment_line or FileContents

        self.charge: int = charge or FileContents
        self.spin_multiplicity: int = spin_multiplicity or FileContents
        self.atoms = atoms or FileContents

        self._output_chk: bool = output_chk

    @classproperty
    def filetype(self) -> str:
        return ".gjf"

    def _find_in_link(self, val: str) -> Optional[int]:
        return next(
            (i for i, l in enumerate(self.link0) if val.lower() in l.lower()),
            None,
        )

    def set_nproc(self, nproc: int):
        nproc = f"nproc={nproc}"
        n = self._find_in_link("nproc")
        if n is None:
            self.link0.append(nproc)
        else:
            self.link0[n] = nproc

    def set_mem(self, mem: str):
        mem = f"mem={mem}"
        n = self._find_in_link("mem")
        if n is None:
            self.link0.append(mem)
        else:
            self.link0[n] = mem

    def add_keyword(self, keyword: str):
        if keyword not in self.keywords:
            self.keywords.append(keyword)

    def add_keywords(self, keywords: List[str]):
        for keyword in keywords:
            self.add_keyword(keyword)

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

    def _set_defaults(self):
        self.link0 = self.link0 or []
        self.method = self.method or ""
        self.basis_set = self.basis_set or ""
        self.keywords = self.keywords or []
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
            while line.strip():
                route_lines.append(line.strip())
                line = next(f)
            route = " ".join(route_lines)

            line = next(f)

            comment_lines_list = []
            while line.strip():
                comment_lines_list.append(line.strip())
                line = next(f)
            comment_line = " ".join(comment_lines_list)

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
        self.comment_line = self.comment_line or comment_line
        self.keywords = self.keywords or route_card.keywords
        self.charge = self.charge or charge
        self.spin_multiplicity = self.spin_multiplicity or spin_multiplicity
        self.atoms = self.atoms or atoms

    def set_write_defaults(self):
        self.link0 = self.link0 or []
        if self._output_chk and any("chk" in l0 for l0 in self.link0):
            self.link0.append(f"chk={self.path.with_suffix('.chk')}")

        self.print_level = self.print_level or PrintLevel.Verbose
        self.method = self.method or "b3lyp"
        self.basis_set = self.basis_set or "6-31+g(d,p)"
        self.keywords = self.keywords or ["nosymm", "output=wfn"]

        self.charge = self.charge or 0
        self.spin_multiplicity = self.spin_multiplicity or 1

    def _write_file(self, path: Path, *args, **kwargs):
        fmtstr = "12.8f"
        self.set_write_defaults()

        with open(path, "w") as f:
            for link0 in self.link0:
                f.write(f"%{link0}\n")
            f.write(
                f"{self.print_level.name} {self.method}/{self.basis_set} {' '.join(self.keywords)}\n"
            )
            f.write("\n")
            f.write(f"{self.path.stem}\n")
            f.write("\n")
            f.write(f"{self.charge}   {self.spin_multiplicity}\n")
            for atom in self.atoms:
                f.write(
                    f"{atom.type} {atom.x:{fmtstr}} {atom.y:{fmtstr}} {atom.z:{fmtstr}}\n"
                )
            if "output=wfn" in self.keywords:
                f.write(f"\n{self.path.with_suffix('.wfn')}")
