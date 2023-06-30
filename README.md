# ICHOR
## Machine Learning Suite for the Popelier Group

[![GitHub release](https://img.shields.io/badge/release-v2.1-blue)](https://github.com/popelier-group/ICHOR/releases/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Website popelier-group.herokuapp.com](https://img.shields.io/website-up-down-green-red/http/shields.io.svg)](https://popelier-group.herokuapp.com/docs/ichor/ichor/)

ICHOR is a program written in python that makes training machine learning models, running programs (Gaussian, AIMALL, DL_FFLUX, AMBER, CP2K, etc.) easier. The idea behind ICHOR is to abstract away the gritty details of running and linking between the programs you use while performing these tasks so if there are features you think are missing or problems that can be made simpler, don't hesitate to create an [issue](https://github.com/popelier-group/ICHOR/issues).
![ICHOR Diagram](doc/img/ICHOR-diagram.png?raw=true "ICHOR Diagram")
## Getting Started
---
The namespace package `ichor` is divided into three parts, `ichor-core`, `ichor-hpc`, and `ichor-cli`. The `ichor-core` sub package contains classes and functions which make it easy to read relevant file and analyze outputs of jobs. The `ichor-hpc` package is used to submit jobs on CSF3, CSF4, and FFLUXLAB. The `ichor-cli` is a command line interface, however it is still not fully working. To get started, only install the `ichor-core` and `ichor-hpc` subpackages (the `hpc` subpackage is only needed when submitting jobs on CSFs and FFLUXLAB, so you do not need to install it when working locally on your machine.)

* Anaconda3 [link](https://www.anaconda.com/distribution/#download-section)
* Gaussian  [link](https://gaussian.com/glossary/g09/)
* AIMAll    [link](http://aim.tkgristmill.com/)
* FEREBUS   [F90](https://github.com/popelier-group/FEREBUS) [Py](https://github.com/popelier-group/pyFEREBUS)
* DL FFLUX  [source](https://github.com/popelier-group/DL_POLY)

#### CSF3
CSF3 provides modules to load programs and set environment variables. ICHOR takes care of these modules when programs are running but the anaconda module is required to run ICHOR initially, this can be loaded using the following:
```
module load apps/binapps/anaconda3/2021.11
```
If you are a new user, to use Gaussian on the CSF, you are required to sign a form and submit to itservices, instructuctions on how to do this and a link to the paperwork can be found [here](http://ri.itservices.manchester.ac.uk/csf3/software/applications/gaussian/).
Contact University research IT services to get access to Gaussian, AMBER, CP2K, etc. as they are already preinstalled on CSF3/4.
#### FFLUXLAB
I currently have modules for my user on ffluxlab which I intend to publish for all users once I am happy that they're stable and get the required permissions. Until then, you can download Anaconda3 using this [link](https://repo.anaconda.com/archive/Anaconda3-2019.10-Linux-x86_64.sh). For setting up the other necessary applications, ask [me](https://github.com/MattBurn) and I will help to get you started.
#### All Machines
Other than Anaconda and Gaussian, a copy of AIMAll, DL FFLUX and FEREBUS is required. AIMAll can be downloaded from [here](http://aim.tkgristmill.com/), again ask [me](https://github.com/MattBurn) about how to download and install AIMAll. AIMAll must be installed in your home directory `~/AIMAll`. Versions of FEREBUS, FEREBUS.py and DL FFLUX are included in the `PROGRAMS` directory in this repository. These binaries were compiled on CSF and so are only guaranteed to work there, for other machines/versions, you will be required to compile your own and place them in this directory under the same name.

#### ICHOR
ICHOR has been designed with as few dependencies as possible. Dependencies are downloaded automatically when installing the sub packages.
If working on CSF3/CSF4, you need to do:

```
module load tools/env/proxy2
```

To be able to access the interned and download packages.
## Installation

If using conda, create a new environment. Please make sure that you are using the latest version of conda on CSF3/CSF4.
Using an older conda version will make it a bit harder to install ichor as the python/setuptools/pip version supplied are older.
Make sure that you have at least python 3.7 in the current environment and that setuptools and pip are all up to date.

On CSF3, you now need to do `qrsh -l short` as the proxy is no longer available. Then, from the submit node, you can access the internet and install packages as needed.

First, download the ICHOR source code. It is recommended to download the code as a git repository, so that you can pull changes from the github code when changes are made. If you download the code as a zip, you will not be able to pull from github and will have to download the code every time a change is made!

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

To install each of the sub-packages, do `python3 -m pip install -e ichor_core_subpackage` to install the `ichor.core` subpackage and `python3 -m pip install -e ichor_hpc_subpackage` to install the hpc subpackage.

The `-e` flag installs the package in `editable` mode, meaning that changes in the ichor source code will be directly made in the installed package. As ichor is still work in progress, it makes it easier to make changes and then test the changes.

```
Note it is usually better to use venv. ON CSF3, activate anaconda first. After that use the python from the anaconda environment to make a venv. After this step is done, you can activate the venv and you no longer need to activate or use conda.
```

## Usage
When you have installed portions of the `ichor` namespace packeg, you can import from the sub-packages like so:

```
from ichor.core import ...
```
or
```
from ichor.hpc import
```
To import specific classes, you can do

```
from ichor.core.atoms import Atoms

atoms_instance = atoms.Atoms()
```
