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
        python_path: ~/miniforge3/envs/ichor_ase/bin/python
        modules: []

That is the path for a Miniforge install in your home directory (see below). If you made
the environment with a cluster's anaconda module instead, it will be under
``~/.conda/envs/ichor_ase`` and ``modules`` needs that anaconda module in it. ``conda env
list`` shows where the environment actually is.

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

Below is a more thorough explanation of how to set up ichor on a compute cluster such as
CSF3 (used by the University of Manchester). Everything here, including downloading and
installing packages, can be done on the login node.

ichor needs Python ``3.10`` or newer. CSF3/CSF4 have a much older Python 3 installed as the
system Python, so you need to get a newer one first.

Recommended: Miniforge
~~~~~~~~~~~~~~~~~~~~~~

`Miniforge <https://github.com/conda-forge/miniforge>`_ is a minimal conda installer which
gets its packages from conda-forge. That is also where ``xtb`` and the PLUMED wrappers for
the ASE jobs come from, so one install covers both ichor and that environment. Install it
in your home directory:

.. code-block:: text

    wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
    bash Miniforge3-Linux-x86_64.sh

Accept the default location (``~/miniforge3``) and answer yes when asked whether to
initialise conda, so that conda is available in new shells and in the submission scripts
of the ASE jobs. Log out and back in (or run ``source ~/.bashrc``), then create and
activate an environment for ichor:

.. code-block:: text

    conda create -n ichor python=3.12
    conda activate ichor

You should see ``(ichor)`` on the left of the terminal, which shows the environment is
active. Activate it like this whenever you use ichor.

Alternative: the cluster's anaconda module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you would rather not install Miniforge, load the newest anaconda module on the cluster
and use its Python to make a ``venv``:

.. code-block:: text

    module load apps/binapps/anaconda3/2024.10
    conda activate
    python3 --version    # must be 3.10 or newer
    python3 -m venv ~/.venv/ichor
    source ~/.venv/ichor/bin/activate

An older anaconda module supplies an older Python, pip and setuptools, which makes
installing ichor harder than it needs to be. Once the venv exists you do not need the
anaconda module to use it, only ``source ~/.venv/ichor/bin/activate``.

Whichever you use, make sure pip and setuptools are up to date before installing ichor:

.. code-block:: text

    python3 -m pip install --upgrade pip setuptools

++++++++++++++++++++++++++++++
Downloading ichor
++++++++++++++++++++++++++++++

Download the ichor source code to your home directory. It is recommended to download the
code as a git repository, so that you can pull changes from GitHub when they are made. If
you download the code as a zip instead, you will have to download it again every time a
change is made.

.. warning::

    You will need to use HTTPS to clone a repository to CSF3/CSF4 as SSH is not supported on the servers.
    Therefore, you will also need to create a Personal Access Token as Github no longer accepts direct password authentication on a server.
    Below are two guides how to clone a repository and create a personal access token

    * `Github Cloning a Repository <https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository>`_
    * `Github Personal Access Token <https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens>`_


With your environment active, install the sub-packages from the top of the repository:

.. code-block:: text

    python3 -m pip install -e ichor_core -e ichor_hpc -e ichor_cli

All three are given to pip at once so that it can resolve the dependencies between them.
The ``-e`` flag installs them in editable mode, so that changes to the source code (such as
those pulled from GitHub) take effect without reinstalling.

Finally, create the config file:

.. code-block:: text

    ichor-config-init

and edit the block for the cluster you are on, as described above. On a SLURM cluster,
``ichor-config-init --detect`` fills in the queue settings for you.

.. warning::

    You will need to have access to the relevant software on the computer cluster if
    submitting jobs with `ichor.hpc` or `ichor.cli`. The paths to those programs, and the
    modules that have to be loaded for them, are what you set in the config file, so they
    need to be right for the cluster you are on and for the versions you have access to.
