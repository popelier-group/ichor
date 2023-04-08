import os


class PythonEnvironmentNotFound(Exception):
    pass


def get_current_python_environment_path():

    venv_env_path = os.getenv("VIRTUAL_ENV")
    conda_env_path = os.getenv("CONDA_PREFIX")

    if venv_env_path is not None:
        return venv_env_path
    elif conda_env_path is not None:
        return conda_env_path
    else:
        raise PythonEnvironmentNotFound("There is no current python environemnt.")
