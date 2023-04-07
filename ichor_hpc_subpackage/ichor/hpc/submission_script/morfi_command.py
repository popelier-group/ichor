from pathlib import Path
from typing import List, Optional

from ichor.core.common.functools import classproperty
from ichor.hpc.modules import Modules
from ichor.hpc.submission_script.aimall_command import AIMAllCommand
from ichor.hpc.submission_script.command_line import CommandLine
from ichor.hpc.submission_script.ichor_command import ICHORCommand
from ichor.hpc.submission_script.pandora_command import PandoraMorfiCommand


class NoInputs(Exception):
    pass


class MorfiCommand(CommandLine):
    def __init__(
        self,
        morfi_input: Path,
        aimall_wfn: Optional[Path] = None,
        point_directory: Optional[Path] = None,
        atoms: Optional[List[str]] = None,
    ):
        self.pandora_command = PandoraMorfiCommand(morfi_input)
        self.aimall_command = (
            AIMAllCommand(aimall_wfn, atoms=atoms) if aimall_wfn is not None else None
        )
        self.point_directory = point_directory

    @classproperty
    def modules(self) -> Modules:
        return PandoraMorfiCommand.modules + AIMAllCommand.modules

    @property
    def ncores(self):
        pass

    @property
    def data(self) -> List[str]:
        data = self.pandora_command.data
        if self.aimall_command is not None:
            data += self.aimall_command.data
        if self.point_directory is not None:
            data += [self.point_directory.absolute()]
        return data

    def command(self) -> str:
        return ""

    def repr(self, variables: List[str]) -> str:
        repr = self.pandora_command.repr(variables[: self.pandora_command.ndata])
        if self.aimall_command is not None:
            repr += "\n"
            repr += self.aimall_command.repr(
                variables[
                    self.pandora_command.ndata : self.pandora_command.ndata
                    + self.aimall_command.ndata
                ]
            )
            if self.point_directory is not None:
                ichor_command = ICHORCommand(
                    func="add_dispersion_to_aimall",
                    func_args=[
                        str(
                            variables[
                                self.pandora_command.ndata + self.aimall_command.ndata
                            ]
                        )
                    ],
                )
                repr += f"{ichor_command.repr()}\n"
        return repr
