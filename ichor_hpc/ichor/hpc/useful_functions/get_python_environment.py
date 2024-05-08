import os
from pathlib import Path
from typing import Union


class PythonEnvironmentPath:
    """Class for storing Python environment paths

    :param venv_env_path: path of a venv / virtualenv environment
    :param conda_env_path: path of a conda environment
    """

    def __init__(
        self, venv_env_path: Union[str, None], conda_env_path: Union[str, None]
    ):

        self.venv_env_path = venv_env_path
        self.conda_env_path = conda_env_path

    @property
    def uses_venv(self) -> bool:
        """If virtualenv /venv are used returns True. Otherwise returns false"""
        if self.venv_env_path is not None:
            return True
        return False

    @property
    def uses_conda(self) -> bool:
        """If conda env is used returns True. Otherwise returns false"""
        if self.conda_env_path is not None:
            return True
        return False

    @property
    def venv_path(self) -> Union[Path, None]:
        """Returns venv environment path or None if not using a conda environment"""
        if self.uses_venv:
            return Path(self.venv_env_path)

    @property
    def conda_path(self) -> Union[Path, None]:
        """Returns conda environment path or None if not using a conda environment"""
        if self.uses_conda:
            return Path(self.conda_env_path)


def get_current_python_environment_path() -> PythonEnvironmentPath:
    """Gets the current active python environment (venv/virtualenv or conda)

    :raises PythonEnvironmentNotFound: If no Python environment is detected.
    :return: PythonEnvironmentPath instance containing Python env info
    """

    venv_env_path = os.getenv("VIRTUAL_ENV")
    conda_env_path = os.getenv("CONDA_PREFIX")

    python_env = PythonEnvironmentPath(venv_env_path, conda_env_path)

    return python_env
