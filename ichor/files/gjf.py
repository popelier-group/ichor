import re
from pathlib import Path
from typing import List, Optional, Union

from ichor import patterns
from ichor.atoms import Atom, Atoms
from ichor.common.functools import buildermethod, classproperty
from ichor.common.io import convert_to_path
from ichor.files.file import FileContents
from ichor.files.qcp import QuantumChemistryProgramInput
from ichor.defaults import gaussian_defaults
from ichor.defaults.gaussian_defaults import GaussianJobType


# TODO: Add:
# - input section
# - freeze atoms
# - oniom?
# - basis-sets?

class GJF(QuantumChemistryProgramInput):
    """Wraps around a .gjf file that is used as input to Gaussian. Below is the usual gjf file structure:

        ----------------------------------------------------------
        %nproc
        %mem
        # <job_type> <method>/<basis-set> <keywords>

        Title

        0 1
        <atom-name> <todo: add -1 for freeze> <x> <y> <z>
        ...

        <todo: input-section>

        <wfn-name>
        -----------------------------------------------------------
    
    :param path: A string or Path to the .gjf file. If a path is not give,
        then there is no file to be read, so the user has to write the file contents. If
        no contents/options are written by user, they are written as the default values in the
        `write` method.
    :param job_type: The job type, an energy, optimization, or frequency
    :param keywords: A list of keywords to be added to the Gaussian keywords line
    :param method: The method to be used by Gaussian (e.g. B3LYP)
    :param basis_set: The basis set to be used by Gaussian (e.g. 6-31+g(d,p))
    :param charge: The charge to be used by Gaussian for the system
    :param multiplicity: The multiplicity to be used by Gaussian for the system.
    :param atoms: An Atoms instance containing a geometry to be written in the .gjf file.
        This is either read in (if an existing gjf path is given) or
        an error is thrown when attempting to write the gjf file (because no gjf file or `Atoms` instance was given)
    :param extra_details_str: A string (can contain multiple lines separated with new line character).
        These will be added to the bottom of the gjf file. This is done in order to handle different basis sets
        for individual atoms, modredundant settings, and other settings that Gaussian handles.
    
    .. note::
        It is up to the user to handle write the `additional_information` settings. ICHOR
        does NOT do checks to see if these additional settings are going to be read in correctly
        in Gaussian.
    """

    def __init__(self, path: Optional[Union[Path, str]],
                startup_options: Optional[List[str]] = FileContents,
                # TODO: job_type needs to be a list because opt freq can be used together.
                job_type: Optional[GaussianJobType] = FileContents,
                keywords: Optional[List[str]] = FileContents,
                method: Optional[str] =  FileContents,
                basis_set: Optional[str] = FileContents,
                charge: Optional[int] = FileContents,
                multiplicity: Optional[int] = FileContents,
                atoms: Atoms = FileContents,
                # TODO: need to read this into a list when reading gjf. Then can be written to new gjf.
                extra_details_str: Optional[str] = FileContents
    ):
        super().__init__(path, method, basis_set, atoms)

        self.startup_options = startup_options
        self.job_type = job_type
        self.keywords = keywords
        self.charge = charge
        self.multiplicity = multiplicity
        self.extra_details_str = extra_details_str

    @buildermethod
    def _read_file(self):
        """Parse and red a .gjf file for information we need to submit a Gaussian job."""
        self.atoms = Atoms()
        with open(self.path, "r") as f:
            for line in f:
                # These are Link 0 Commands in Gaussian, eg. %chk
                if line.startswith("%"):
                    if self.startup_options is FileContents:
                        self.startup_options = []
                    self.startup_options += [line.strip().replace("%", "")]
                # This is the following line where key words for Gaussian (level of theory, etc.) are defined
                elif line.startswith("#"):
                    line = line.replace("#", "")
                    keywords = line.split()  # split keywords by whitespace
                    for keyword in keywords:
                        if (
                            "/" in keyword
                        ):  # if the user has used something like B3LYP/6-31G Then split them up
                            self.method = keyword.split("/")[0].upper()
                            self.basis_set = keyword.split("/")[1].lower()
                        # if the keyword is in the job enum GaussianJobType: p, opt, freq
                        elif keyword in GaussianJobType.types():
                            for ty in GaussianJobType:
                                if keyword == ty:
                                    # set self.job_type to the enum value corresponding to the keyword
                                    self.job_type = ty
                                    break
                        # if the given Gaussian keyword is not defined in GaussianJobType or is not level of theory/basis set
                        # then add to self.keywords which is None by Default
                        else:
                            if self.keywords is FileContents:
                                self.keywords = []
                            self.keywords += [keyword]
                # find charge and multiplicity which are given on one line in Gaussian .gjf
                elif re.match(r"^\s*\d+\s+\d+\s*$", line):
                    self.charge = int(line.split()[0])
                    self.multiplicity = int(line.split()[1])
                # find all the types of atoms as well as their coordinates from .gjf file
                elif re.match(patterns.COORDINATE_LINE, line):
                    line_split = line.strip().split()
                    atom_type, x, y, z = (
                        line_split[0],
                        float(line_split[1]),
                        float(line_split[2]),
                        float(line_split[3]),
                    )
                    # add the coordinate line as an Atom instance to self.atoms (which is an Atoms instance)
                    self.atoms.add(Atom(atom_type, x, y, z))

    @classproperty
    def filetype(cls) -> str:
        """Returns the extension of the GJF file."""
        return ".gjf"

    @property
    def title(self) -> str:
        """returns the name of the file, without the suffix (eg. WATER.gjf will return WATER)."""
        return self.path.stem

    @property
    def wfn(self) -> Path:
        """The name of the .wfn file to be returned by Gaussian."""
        return self.path.with_suffix(".wfn")

    @property
    def header_line(self) -> str:
        """Returns a string that is the line in the gjf file that contains all keywords."""
        return f"#{self.job_type.value} {self.method}/{self.basis_set} {' '.join(map(str, self.keywords))}\n"

    @convert_to_path
    def write(self, path: Path = "GJF_FILE.gjf") -> None:
        """Write the .gjf file to disk. This overwrites .gjf files that currently exist in the path to add any extra options that
        should be given to Gaussian."""

        if not self.atoms:
            raise ValueError(f"self.atoms is currently {self.atoms}. Cannot write coordinates.")

        # TODO: can probably make a for loop here and loop over the vars which are FileContents and set to default
        # give default values to each one of these if the value is FileContents (which evaluates to False).
        path = self.path or path
        self.startup_options = self.startup_options or gaussian_defaults.startup_options
        # TODO: make this into a list because can use opt and freq at the same time
        self.job_type = self.job_type or gaussian_defaults.job_type
        # if self.keywords evaluates to False, then default keywords are used (even if they are [])
        self.keywords = self.keywords or gaussian_defaults.keywords
        self.method = self.method or gaussian_defaults.method
        self.basis_set = self.basis_set or gaussian_defaults.basis_set
        self.charge = self.charge or gaussian_defaults.charge
        self.multiplicity = self.multiplicity or gaussian_defaults.multiplicity

        # remove whitespace from keywords and lowercase to prevent having keywords twice.
        self.keywords = ["".join(k.lower().split()) for k in self.keywords]
        # remove any duplicates by converting to set then list
        self.keywords = list(set(self.keywords))

        with open(path, "w") as f:
            # TODO: the self.format() results in NoFileFound because of the `class File` implementation. So it has to be inside here.
            for startup_option in self.startup_options:
                f.write(f"%" + startup_option + "\n")
            f.write(f"{self.header_line}\n")
            f.write(f"{self.title}\n\n")
            f.write(f"{self.charge} {self.multiplicity}\n")
            for atom in self.atoms:
                f.write(f"{atom.type} {atom.coordinates_string}\n")
            if self.extra_details_str:
                f.write(f"\n{self.extra_details_str}\n")
            f.write(f"\n{self.wfn}")
