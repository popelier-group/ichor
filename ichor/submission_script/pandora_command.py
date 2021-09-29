from pathlib import Path
from typing import List, Optional

from ichor.common.functools import classproperty
from ichor.globals import GLOBALS
from ichor.modules import Modules, PandoraModules
from ichor.submission_script.python_command import PythonCommand
from ichor.submission_script.ichor_command import ICHORCommand
from ichor.pandora import PANDORA_LOCATION
from ichor.files import PandoraDirectory


class PandoraCommand(PythonCommand):
    def __init__(
        self, config_file: Path, pyscf: bool = True, morfi: bool = True
    ):
        self.config_file = config_file
        self.run_pyscf = pyscf
        self.run_morfi = morfi

        self._args = []

        PythonCommand.__init__(self, Path(PANDORA_LOCATION()).absolute())

    @classproperty
    def modules(self) -> Modules:
        return PythonCommand.modules + PandoraModules

    @property
    def data(self) -> List[str]:
        return [f"{self.config_file.absolute()}"]

    @property
    def args(self) -> List[str]:
        if self.run_pyscf and '--pyscf' not in self._args:
            self._args.append("--pyscf")
        if self.run_morfi and '--morfi' not in self._args:
            self._args.append("--morfi")
        return self._args

    @args.setter
    def args(self, value):
        self._args = value

    def repr(self, variables: List[str]) -> str:
        repr = f"pushd $(dirname {variables[0]})\n"
        repr += f"{PythonCommand.command} {self.script} {variables[0]} {' '.join(self.args)}\n"
        repr += "popd"
        return repr


class PandoraPySCFCommand(PandoraCommand):
    def __init__(self, config_file: Path, point_directory: Optional[Path] = None):
        PandoraCommand.__init__(self, config_file, pyscf=True, morfi=False)
        self.point_directory = point_directory

    @property
    def data(self) -> List[str]:
        data = super().data
        if self.point_directory is not None:
            data.append(self.config_file.parent / PandoraDirectory.dirname)
            data.append(self.point_directory)
        return data

    def repr(self, variables: List[str]) -> str:
        repr = super().repr(variables)
        if self.point_directory is not None:
            ichor_command = ICHORCommand(func='copy_aimall_wfn_to_point_directory', func_args=[variables[1], variables[2]])
            repr += f'\n{ichor_command.repr(variables)}'
        return repr


class PandoraMorfiCommand(PandoraCommand):
    def __init__(self, config_file: Path):
        super().__init__(config_file, pyscf=False, morfi=True)
