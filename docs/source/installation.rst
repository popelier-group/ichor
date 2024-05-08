Installing ichor
----------------

++++++++++++++++++++++++++++++
Setting up Python environments
++++++++++++++++++++++++++++++


.. warning::

    You will need to make separate environments for CSF3 and CSF4.

    For CSF3 use ``source activate my_env`` to activate a CONDA environment in both the login node and when submitting jobs.
    Check out the guide here. Not sure why this is required.

    * `Anaconda CSF3 <https://ri.itservices.manchester.ac.uk/csf3/software/applications/anaconda-python/>`_

CSF3/CSF4 have a very old Python 3 installed, so you will need to load in an anaconda module file to gain access to recent python versions.
Please make sure that you are using the latest version of conda on CSF3/CSF4.
At the time of writing this guide, the latest version of Python with conda is ``3.9``. Using an older conda version will make it harder to install ichor as the python/setuptools/pip version supplied are older.

To load conda, use

.. code-block:: text

    module load apps/binapps/anaconda3/2022.10

To activate the ``base`` conda environment, which should have Python ``3.9`` with the above module, do

.. code-block:: text

    conda activate

and you should see a ``(base)`` on the left of the terminal, you can check the version by doing ``python3 --version``.

On CSF3, you need to do ``qrsh -l short`` as the network proxy is no longer available.
This goes into a submit (compute) node, you can access the internet and install packages as well as make new conda environments with different python versions.

.. warning::

    You will need to load in the anaconda module and activate the environment again in the
    compute node to be able to install packages in the correct environment.
    Create environments while in the compute node which has internet access. After you have installed all the packages,
    then you can exit out of the compute node and should be able to load in the environment on the login node.
    You should be able to submit jobs now on the login node using the Python environment made on the compute node.

To make a conda environment (with the appropriate conda module loaded on csf3/csf4) do

.. code-block:: text

    conda create -n ichor

This will create a new environment with the Python version from the base environment.

To activate the conda environment do ``conda activate name_of_env``. Note that you can specify the Python version in these conda environments as well,
just make sure to be on the compute node because it has to download things from the internet.

Now you can make a ``venv`` environment which will use the Python version from the activated conda environment. To make a venv, do

.. code-block:: text

    python3 -m venv ~/.venv/ichor

This creates a virtual environment in the ``~/.venv/ichor`` folder and all environment packages will be installed here.
To active the venv environment, do ``source ~/.venv/env_name/bin/activate``. Use this is you have problems with the anaconda for some reason or problems installing packages in anaconda.

.. note::

    You will not need the conda module anymore if using venv. If you make a venv environment, the python version will be
    taken from the conda environment (so we are going to be using the same python version available in the conda environment),
    however, all packages will now be installed in the venv environment instead of the conda environment. This should remove
    problems associated with anaconda / loading anaconda modules.

You should see ``(ichor)`` show up on the left side of the terminal, which indicates you are in the ``ichor`` environment. This is the
same for both venv and conda.

Make sure that you have at least python 3.7 in the current venv or conda environment and that setuptools and pip are all up to date.

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


To install each of the sub-packages, do

.. code-block:: python

    python3 -m pip install -e ichor_core
    python3 -m pip install -e ichor_hpc
    python3 -m pip install -e ichor_cli

Please install these in the given order, as there are dependencies between the packages.

The ``-e`` flag installs the package in editable mode,
meaning that changes in the ichor source code will be directly made in the installed package. As ichor is still work in progress, it makes it easier to make changes and then test the changes.

.. warning::

    You will need to have access to the relevant
    software on the computer cluster if submitting jobs with `ichor.hpc` or
    `ichor.cli`. Currently, the paths to programs are hard coded into the ichor code, so
    they will need to exist at the correct paths.

    Also, make sure that you have access to the right versions of the software
    on the right cluster.

.. note::

    You need to be connected to the internet to be able to download and install the relevant
    dependencies of ichor.

.. note::

    Note it is usually better to use venv.
    On CSF3, activate anaconda first. After that use the python from the anaconda environment to make a venv. After this step is done, you can activate the venv and you no longer need to activate or use conda.
