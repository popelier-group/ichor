Installing ichor
----------------

If using conda, create a new environment. Please make sure that you are using the latest version of conda on CSF3/CSF4.
Using an older conda version will make it a bit harder to install ichor as the python/setuptools/pip version supplied are older.
Make sure that you have at least python 3.7 in the current environment and that setuptools and pip are all up to date.

On CSF3, you now need to do `qrsh -l short` as the proxy is no longer available. Then, from the submit node, you can access the internet and install packages as needed.

First, download the ICHOR source code. It is recommended to download the code as a git repository,
so that you can pull changes from the github code when changes are made.
If you download the code as a zip, you will not be able to pull from github and will have to download the code every time a change is made!

To make a conda environment do

```
conda create -n ichor
```

To activate the conda environment do `conda activate name_of_env`.

Use can also use a `venv` environment. To make a venv, do

```
python3 -m venv ~/.venv/ichor
```

This activate this environment, do `source ~/.venv/env_name/bin/activate`. Use this is you have problems with the anaconda for some reason or problems installing packages in anaconda.


This will make a new environment called `ichor`, which can be activated by doing `conda activate ichor`. You should see `(ichor)` show up on the left side of the terminal, which indicates you are in the `ichor` environment.

To install each of the sub-packages, do

.. code-block:: python
python3 -m pip install -e ichor_core_subpackage
python3 -m pip install -e ichor_hpc_subpackage
python3 -m pip install -e ichor_cli_subpackage

Please install these in the given order, as there are dependencies between the packages.

The `-e` flag installs the package in `editable` mode,
meaning that changes in the ichor source code will be directly made in the installed package. As ichor is still work in progress, it makes it easier to make changes and then test the changes.

**You need to be connected to the internet to be able to download and install the relavant
dependencies of ichor**.

```
Note it is usually better to use venv. ON CSF3, activate anaconda first. After that use the python from the anaconda environment to make a venv. After this step is done, you can activate the venv and you no longer need to activate or use conda.
```
