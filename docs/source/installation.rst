Installing ichor
----------------

To install ichor, simply do

.. code-block:: text

    python3 -m pip install -e ichor_core -e ichor_hpc -e ichor_cli

This will install all the packages in editable mode, so that any changes to the source code will
be available to the user directly.

.. note::

    All three packages are installed with a single command. ``ichor-hpc`` and ``ichor-cli``
    depend on ``ichor-core``, which is not published on PyPI, so pip can only satisfy those
    dependencies if all three are given to it at once. Installing them one at a time fails
    unless it happens to be done in the right order.

++++++++++++++++++++++++++++++++++++++
The conda environment for the ASE jobs
++++++++++++++++++++++++++++++++++++++

The ASE optimisation and metadynamics jobs do not run in ichor's environment. The
scripts ichor writes for them import ``ase``, ``xtb`` and (for metadynamics)
``plumed``, and import nothing from ichor, so they run in a conda environment of
their own which the submission script activates.

They get their own environment because ``xtb`` and the PLUMED Python wrappers are
only distributed for current Python versions through conda-forge -- the ``xtb``
wheels on PyPI stop at CPython ``3.11``. Keeping them out of ichor's own
dependencies is what lets ichor be installed with pip on any supported Python.

Create the environment from the ``environment.yml`` in the ichor repository:

.. code-block:: text

    conda env create -f environment.yml

Then tell ichor where it is, in the block for the machine you are on in your config
file:

.. code-block:: text

    software:
      python:
        env_name: ichor_ase
        python_path: ~/.conda/envs/ichor_ase/bin/python
        modules: [<the anaconda module for this cluster>]

Which environment each kind of job uses:

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Job
     - Environment
     - What the script imports
   * - ASE optimisation
     - the conda environment above
     - ``ase``, ``xtb``
   * - Metadynamics
     - the conda environment above
     - ``ase``, ``xtb``, ``plumed``, ``numpy``
   * - polus sampling
     - ichor's own environment
     - ``polus``, ``numpy``
   * - Everything else
     - ichor's own environment
     - ichor itself

.. note::

    ichor checks that this environment exists and has what the job imports *before*
    submitting anything, so a missing package is reported on the login node rather
    than turning up as a ``ModuleNotFoundError`` in a job error file later on.

++++++++++++++++++++++++++
Setting up the config file
++++++++++++++++++++++++++

The config file stores settings for the high performance computing (HPC) clusters. It is
needed if you are using `ichor.hpc` and `ichor.cli` as these interface with the workload
manager on the HPC cluster. To create one, run

.. code-block:: text

    ichor-config-init

which writes an example config file to ``~/.config/ichor/config.yaml`` and prints the path
it wrote to. Edit the block for the cluster you are on before submitting any jobs.

One config file covers every cluster, as each top level key is the name of a machine and
ichor selects the block whose name appears in the hostname. There is no need for a separate
config file, or a separate Python environment, per cluster.

If you already have an ``~/ichor_config.yaml`` from an older version of ichor, the same
command moves it to the new location. That old location is still read, so nothing breaks
straight away, but it warns and should be migrated.

See :doc:`ichor_config_setup` for what goes in the file and for the full list of locations
that are searched.

++++++++++++++++++++++++++++++
Setting up Python environments
++++++++++++++++++++++++++++++

Below is a more thorough explanation on how to set up ichor on a compute cluster such as CSF3 (used by the University of Manchester).

ichor needs Python ``3.10`` or newer. CSF3/CSF4 have a much older Python 3 installed as the
system Python, so you will need to load an anaconda module file to get a recent enough
version. Use the newest anaconda module available on the cluster: an older one supplies an
older pip and setuptools, which makes installing ichor harder than it needs to be.

To load conda, use

.. code-block:: text

    module load apps/binapps/anaconda3/2024.10

To activate the ``base`` conda environment, do

.. code-block:: text

    conda activate

and you should see a ``(base)`` on the left of the terminal. Check the version with
``python3 --version`` and make sure it is ``3.10`` or newer before going any further --
if it is not, load a newer anaconda module.

On CSF3, you need to do ``qrsh -l short`` as the network proxy is no longer available.
This goes into a submit (compute) node, you can access the internet and install packages as well as make new conda environments with different python versions.

.. warning::

    You will need to load in the anaconda module and activate the environment again in the
    compute node to be able to install packages in the correct environment.
    Create environments while in the compute node which has internet access. After you have installed all the packages,
    then you can exit out of the compute node and should be able to load in the environment on the login node.
    You should be able to submit jobs now on the login node using the Python environment made on the compute node.

Now you can make a ``venv`` environment which will use the Python version from the activated conda environment. To make a venv, do

.. code-block:: text

    python3 -m venv ~/.venv/ichor

This creates a virtual environment in the ``~/.venv/ichor`` folder and all environment packages will be installed here.
To active the venv environment, do ``source ~/.venv/env_name/bin/activate``. Use this is you have problems with the anaconda for some reason or problems installing packages in anaconda.
To activate on GitBash, do ``. ~/.venv/ichor/Scripts/activate``.

.. note::

    You will not need the conda module anymore if using venv. If you make a venv environment, the python version will be
    taken from the conda environment (so we are going to be using the same python version available in the conda environment),
    however, all packages will now be installed in the venv environment instead of the conda environment. This should remove
    problems associated with anaconda / loading anaconda modules.

You should see ``(ichor)`` show up on the left side of the terminal, which indicates you are in the ``ichor`` environment. This is the
same for both venv and conda.

Make sure that the venv or conda environment has Python ``3.10`` or newer, and that setuptools and pip are up to date.

To make sure you are using the latest versions of the packages, use

.. code-block:: text

    python3 -m pip install --upgrade pip setuptools

++++++++++++++++++++++++++++++
Downloading ichor
++++++++++++++++++++++++++++++

First, download the ichor source code to your home directory (again you need to be on the compute node to have internet access). It is recommended to download the code as a git repository,
so that you can pull changes from the github code when changes are made. You can follow the Github guides on how to clone.
If you download the code as a zip, you will not be able to pull from github and will have to download the code every time a change is made!

.. warning::

    You will need to use HTTPS to clone a repository to CSF3/CSF4 as SSH is not supported on the servers.
    Therefore, you will also need to create a Personal Access Token as Github no longer accepts direct password authentication on a server.
    Below are two guides how to clone a repository and create a personal access token

    * `Github Cloning a Repository <https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository>`_
    * `Github Personal Access Token <https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens>`_


To install the sub-packages, do

.. code-block:: text

    python3 -m pip install -e ichor_core -e ichor_hpc -e ichor_cli

All three are given to pip at once so that it can resolve the dependencies between them.

The ``-e`` flag installs the package in editable mode,
meaning that changes in the ichor source code will be directly made in the installed package. As ichor is still work in progress, it makes it easier to make changes and then test the changes.

Finally, create the config file:

.. code-block:: text

    ichor-config-init

and edit the block for the cluster you are on, as described above.

.. warning::

    You will need to have access to the relevant software on the computer cluster if
    submitting jobs with `ichor.hpc` or `ichor.cli`. The paths to those programs, and the
    modules that have to be loaded for them, are what you set in the config file, so they
    need to be right for the cluster you are on and for the versions you have access to.

.. note::

    You need to be connected to the internet to be able to download and install the relevant
    dependencies of ichor.

.. note::

    Note it is usually better to use venv.
    On CSF3, activate anaconda first. After that use the python from the anaconda environment to make a venv. After this step is done, you can activate the venv and you no longer need to activate or use conda.
