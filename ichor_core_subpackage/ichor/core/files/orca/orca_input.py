from pathlib import Path
from typing import Dict, List, Optional, Union

from ichor.core.atoms import Atom, Atoms
from ichor.core.common.pairwise import pairwise

from ichor.core.files.file import File, FileContents, ReadFile, WriteFile
from ichor.core.files.file_data import HasAtoms


class OrcaInput(ReadFile, WriteFile, File, HasAtoms):
    """
    Wraps around an ORCA input file that is used as input to ORCA.

    :param path: A string or Path to the ORCA input file file. If a path is not give,
        then there is no file to be read, so the user has to write the file contents. If
        no contents/options are written by user, they are written as the default values in the
        ``write`` method.
    :param method: The method to use for calculation, defaults to b3lyp/g if not given
    :param basis_set: The basis set for the calculation, defaults to "6-31+g(d,p)"
    :param main_input: A list of strings which are commands beginning with !
        charge: Optional[int] = None,
        spin_multiplicity: Optional[int] = None,
        atoms: Optional[Atoms] = None,
        input_blocks: Dict[str, Union[str, List[str]]]
    :param charge: The charge of the system
    :param spin_multiplicity: The spin multiplicity of the system
    :param atoms: An Atoms instance that contains the molecular structure
    :param input_blocks: A dictionary consisting of keys: The option,
        and values: A list containing even number of elements. The option
        is going to be written out with a %, followed by the specifications
        that the user gives for the option

    .. note::
        There is no checking of what the inputs are, so it is up to the user to make sure
        that the inputs are correct.

    .. note::
        Gaussian uses a different b3lyp version (https://sites.google.com/site/orcainputlibrary/dft-calculations)
        so use b3lyp/g (this is the Gaussian implementation) instead of b3lyp

    References:
        https://sites.google.com/site/orcainputlibrary/home
        https://www.cup.uni-muenchen.de/oc/zipse/teaching/computational-chemistry-2/topics/a-typical-orca-output-file/
        https://www.orcasoftware.de/tutorials_orca/first_steps/input_output.html
        https://www.afs.enea.it/software/orca/orca_manual_4_2_1.pdf (note this is for version 4, not 5)
        version 5 manual, needs login:
        available in https://orcaforum.kofo.mpg.de/app.php/dlext/?view=detail&df_id=186
        https://orcaforum.kofo.mpg.de/viewtopic.php?f=8&t=7470&p=32102&hilit=atomic+force#p32102
    """

    _filetype = ".orcainput"

    def __init__(
        self,
        path: Union[Path, str],
        method: Optional[str] = None,
        basis_set: Optional[str] = None,
        main_input: Optional[List[str]] = None,
        charge: Optional[int] = None,
        spin_multiplicity: Optional[int] = None,
        atoms: Optional[Atoms] = None,
        **input_blocks: Dict[str, Union[str, List[str]]],
    ):
        File.__init__(self, path)

        # have the method and basis set separately because they
        # are the most important bits
        self.method: str = method or FileContents
        self.basis_set: str = basis_set or FileContents
        # the main input contains lines starting with !
        self.main_input: List[str] = main_input or FileContents
        self.charge: int = charge or FileContents
        self.spin_multiplicity: int = spin_multiplicity or FileContents
        self.atoms = atoms or FileContents

        # any other input blocks specified by %
        self.input_blocks = input_blocks or FileContents

    def _read_file(self):

        with open(self.path, "r") as f:
            # assume the first lines start with !
            # the next lines are optional commands with %
            # and finally the inputs

            line = next(f)

            main_input = []
            # these are lines that contain things like method and basis set
            # since these can be on multiple lines

            while line.strip().startswith("!"):
                line = line.lower()
                line = line.strip().replace("!", "")
                line_splits = line.split()
                for s in line_splits:
                    main_input.append(s)
                line = next(f)

            # assume the method is the first line
            # and the basis set is the second line
            method, basis_set = main_input[0], main_input[1]
            # remove the main input first and second elements
            # which are the method and basis set
            del main_input[0:2]

            # used for cases when there are no options with %
            _reached_end = False
            input_blocks = {}
            # while we are not at the geometries
            while not line.strip().startswith("*"):

                line = line.lower()
                one_option = []
                # now read in optional input with %
                # the not line.strip().startswith("*") is in case there are no options
                while "end" not in line.strip():
                    if not line.strip().startswith("*"):
                        one_option.append(line)
                        line = next(f)
                        line = line.lower()
                    else:
                        _reached_end = True
                        break
                if not _reached_end:
                    line = next(f)

                # this will be the option name and all other options
                # given on lines on or after the option name
                # until an end statement is reached
                tmp = one_option[0].strip().replace("%", "").split()
                # if there are no options, then tmp is an empty list
                # so this will not get called
                if tmp:
                    option_name, *other_options = tmp
                    input_blocks[option_name] = other_options
                    for other_lines in one_option[1:]:
                        input_blocks[option_name] += other_lines.strip().split()

            charge, spin_multiplicity = map(int, line.strip().split()[-2:])
            line = next(f)
            atoms = Atoms()
            while line.strip() and line.strip() != "*":
                atoms.append(Atom(*line.split()))
                try:
                    line = next(f)
                except StopIteration:
                    break

        self.method = self.method or method
        self.basis_set = self.basis_set or basis_set
        self.main_input = self.main_input or main_input
        self.input_blocks = self.input_blocks or input_blocks
        self.charge = self.charge or charge
        self.spin_multiplicity = self.spin_multiplicity or spin_multiplicity
        self.atoms = self.atoms or atoms

    def _set_write_defaults_if_needed(self):
        """Set default values for attributes if bool(self.attribute) evaluates to False.
        So if an attribute is still FileContents, an empty string, an empty list, etc.,
        then default values will be used."""

        self.method = self.method or "b3lyp/g"
        self.basis_set = self.method or "6-31+g(d,p)"

        # aim for wfn file
        # nousesym to not use symmetry
        # normalprint for printing out to the outputfile
        # engrad calculate energy and (analytical) gradient
        self.main_input = self.main_input or [
            "nousesym",
            "aim",
            "normalprint",
            "engrad",
        ]

        # have to have default values for input blocks
        self.input_blocks = self.input_blocks or {}

        self.charge = self.charge or 0
        self.spin_multiplicity = self.spin_multiplicity or 1

    def _check_values_before_writing(self):
        """Basic checks done prior to writing file.

        .. note:: Not everything written to file can be checked for, so
        there is still the need for a user to check out what is being written.
        """

        if len(self.atoms) == 0:
            raise ValueError("There are no atoms to write to orca input file.")

    def _write_file(self, path: Path, *args, **kwargs):
        fmtstr = "12.8f"

        write_str = ""

        write_str += f"!{self.method}\n"
        write_str += f"!{self.basis_set}\n"
        for m in self.main_input:
            write_str += f"!{m}\n"
        for k, vals in self.input_blocks.items():
            write_str += f"%{k}\n"
            for v in pairwise(vals):
                write_str += f"    {v[0]} {v[1]}\n"
            write_str += "end"
        write_str += "\n"
        write_str += f"* xyz {self.charge} {self.spin_multiplicity}\n"
        for atom in self.atoms:
            write_str += (
                f"{atom.type} {atom.x:{fmtstr}} {atom.y:{fmtstr}} {atom.z:{fmtstr}}\n"
            )
        write_str += "*"

        return write_str
