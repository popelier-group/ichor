import re
from pathlib import Path
from typing import List, Optional, Union

from ichor.core import patterns
from ichor.core.atoms import Atom, Atoms
from ichor.core.common.functools import buildermethod, classproperty
from ichor.core.common.io import convert_to_path
from ichor.core.files.file import FileContents
from ichor.core.files.qcp import QuantumChemistryProgramInput
from ichor.core.program_defaults import gaussian_defaults
from ichor.core.program_defaults.gaussian_defaults import GaussianJobType


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
        startup_options: List[str] = FileContents,
        comment_line: Optional[str] = FileContents,
        # TODO: job_type needs to be a list because opt freq can be used together.
        job_type: List[GaussianJobType] = FileContents,
        keywords: List[str] = FileContents,
        method: str = FileContents,
        basis_set: str = FileContents,
        charge: int = FileContents,
        multiplicity: int = FileContents,
        atoms: Atoms = FileContents,
        extra_details_str: Optional[str] = FileContents,
    ):
        super().__init__(path, method, basis_set, atoms)

        self.startup_options = startup_options
        self.comment_line = comment_line
        self.job_type = job_type
        self.keywords = keywords
        self.charge = charge
        self.multiplicity = multiplicity
        self.extra_details_str = extra_details_str

    @buildermethod
    def _read_file(self):
        """Parse and red a .gjf file for information we need to submit a Gaussian job."""

        with open(self.path, "r") as f:
            # go to very first line
            line = next(f)
            # These are Link 0 Commands in Gaussian, eg. %chk
            read_starup_options = []
            while line.startswith("%"):
                read_starup_options += [line.strip().replace("%", "")]
                line = next(f)
            self.startup_options = self.startup_options or read_starup_options
            # This is the following line where key words for Gaussian (level of theory, etc.) are defined
            # comes right after the Link 0 options
            if line.startswith("#"):
                line = line.replace("#", "")
                keywords = line.split()  # split keywords by whitespace
                # remove this as it is not a keyword, just used to print out more stuff to output file
                if "p" in keywords:
                    keywords.remove("p")
                read_job_type = []
                read_keywords = []
                for keyword in keywords:
                    if (
                        "/" in keyword
                    ):  # if the user has used something like B3LYP/6-31G Then split them up
                        self.method = self.method or keyword.split("/")[0]
                        self.basis_set = (
                            self.basis_set or keyword.split("/")[1]
                        )

                    # if the keyword is in the job enum GaussianJobType: opt, freq
                    elif keyword in GaussianJobType.types():
                        read_job_type.append(GaussianJobType(keyword))
                    # if the given Gaussian keyword is not defined in GaussianJobType or is not level of theory/basis set
                    # then add to keywords which is None by Default
                    else:
                        read_keywords.append(keyword)

                # if opt or freq are not read, then assume single point type calculation
                if len(read_job_type) == 0:
                    read_job_type = GaussianJobType.SinglePoint

                self.job_type = self.job_type or read_job_type
                self.keywords = self.keywords or read_keywords

            # line following keywords line is blank line
            line = next(f)
            # following blank line is a comment line that can contain anything
            line = next(f)
            self.comment_line = self.comment_line or line.strip()
            # following this comment line is another blank line
            line = next(f)
            # next line contains charge and multiplicity
            line = next(f)
            if re.match(r"^\s*\d+\s+\d+\s*$", line):
                self.charge = self.charge or int(line.split()[0])
                self.multiplicity = self.multiplicity or int(line.split()[1])
            # find all the types of atoms as well as their coordinates from .gjf file
            line = next(f)
            read_atoms = Atoms()
            while re.match(patterns.COORDINATE_LINE, line):
                line_split = line.strip().split()
                atom_type, x, y, z = (
                    line_split[0],
                    float(line_split[1]),
                    float(line_split[2]),
                    float(line_split[3]),
                )
                # add the coordinate line as an Atom instance to atoms (which is an Atoms instance)
                read_atoms.add(Atom(atom_type, x, y, z))
                line = next(f)

            self.atoms = self.atoms or read_atoms

            # read in extra options at the bottom of file. These begin directly after coordinates (including blank line)
            read_extra_details_string_list = []
            while line:
                read_extra_details_string_list.append(line)
                line = next(
                    f, ""
                )  # the empty string which is returned instead of StopIteration, "" evaluates as False
            # if there are stuff from the bottom of the file, then we have extra details to write
            # at bottom of gjf file
            if len(read_extra_details_string_list) > 0:
                # join line into one string that can be written following coordinates
                read_extra_details_str = "".join(
                    read_extra_details_string_list
                )
            else:
                # otherwise just add 3 empty lines at bottom of file just in case to prevent read errors in Gaussian
                read_extra_details_str = "".join(["\n" for n in range(3)])

            self.extra_details_str = (
                self.extra_details_str or read_extra_details_str
            )

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
        job_type = " ".join([val.value for val in self.job_type])
        return f"#p {self.method}/{self.basis_set} {job_type} {' '.join(map(str, self.keywords))}\n"

    @convert_to_path
    def write(self, path: Optional[Union[str, Path]] = None):
        """Write the .gjf file to disk. This overwrites .gjf files that currently exist in the path to add any extra options that
        should be given to Gaussian.

        :param path: A path where to write file. If no path is given here, the value of
        `self.path` attribute is used.
        """
        # where to write files
        if path:
            p = path
        else:
            p = self.path

        if not self.atoms:
            raise ValueError(
                f"self.atoms is currently {self.atoms}. Cannot write coordinates."
            )

        # TODO: can probably make a for loop here and loop over the vars which are FileContents and set to default
        # give default values to each one of these if the value is FileContents (which evaluates to False).
        self.startup_options = (
            self.startup_options or gaussian_defaults.startup_options
        )
        self.comment_line = self.comment_line or self.title
        # TODO: make this into a list because can use opt and freq at the same time
        self.job_type = self.job_type or gaussian_defaults.job_type
        # if self.keywords evaluates to False (because it is FileContents), then default keywords are used (even if defaults are are [])
        self.keywords = self.keywords or gaussian_defaults.keywords
        self.method = self.method or gaussian_defaults.method
        self.basis_set = self.basis_set or gaussian_defaults.basis_set
        self.charge = self.charge or gaussian_defaults.charge
        self.multiplicity = self.multiplicity or gaussian_defaults.multiplicity
        # use function here as the default string depends of self.path
        self.extra_details_str = (
            self.extra_details_str
            or gaussian_defaults.extra_details_str_fnc(self.path)
        )

        # remove whitespace from keywords and lowercase to prevent having keywords twice.
        self.keywords = ["".join(k.lower().split()) for k in self.keywords]
        # remove any duplicates by converting to set then list. Keep original ordering, so don't use set.
        self.keywords = list(dict.fromkeys(self.keywords))

        with open(p, "w") as f:
            # TODO: the self.format() results in NoFileFound because of the `class File` implementation. So it has to be inside here.
            for startup_option in self.startup_options:
                f.write(f"%" + startup_option + "\n")
            f.write(f"{self.header_line}\n")
            f.write(f"{self.comment_line}\n\n")
            f.write(f"{self.charge} {self.multiplicity}\n")
            for atom in self.atoms:
                f.write(f"{atom.type} {atom.coordinates_string}\n")
            if self.extra_details_str:
                f.write(f"{self.extra_details_str}")
