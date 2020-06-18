# ICHOR
## Machine Learning Suite for the Popellier Group

[![GitHub release](https://img.shields.io/badge/release-v2.1-blue)](https://github.com/popelier-group/ICHOR/releases/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Website popelier-group.herokuapp.com](https://img.shields.io/website-up-down-green-red/http/shields.io.svg)](https://popelier-group.herokuapp.com/ichor/ichor/)

ICHOR is a program written in python that makes training machine learning models, adaptive sampling and running DL_FFLUX as simple as the press of a button. The idea behind ICHOR is to abstract away the gritty details of running and linking between the programs you use while performing these tasks so if there are features you think are missing or problems that can be made simpler, don't hesitate to create an [issue](https://github.com/popelier-group/ICHOR/issues).
![ICHOR Diagram](doc/img/ICHOR-diagram.png?raw=true "ICHOR Diagram")
## Getting Started
---
ICHOR has been designed to work on the CSF and FFLUXLAB, I am looking into adding support for local machines in the future but until then, only some features will work. To fully setup ICHOR, 5 applications are need to be setup:
* Anaconda3 [link](https://www.anaconda.com/distribution/#download-section)
* Gaussian  [link](https://gaussian.com/glossary/g09/)
* AIMAll    [link](http://aim.tkgristmill.com/)
* FEREBUS   [F90](https://github.com/popelier-group/FEREBUS) [Py](https://github.com/popelier-group/pyFEREBUS)
* DL FFLUX  [source](https://github.com/popelier-group/DL_POLY)
### Prerequisites
#### CSF3
CSF3 provides modules to load programs and set environment variables. ICHOR takes care of these modules when programs are running but the anaconda module is required to run ICHOR initially, this can be loaded using the following:
```
module load apps/anaconda3.5.2.0/bin
```
If you are a new user, to use Gaussian on the CSF, you are required to sign a form and submit to itservices, instructuctions on how to do this and a link to the paperwork can be found [here](http://ri.itservices.manchester.ac.uk/csf3/software/applications/gaussian/).
#### FFLUXLAB
I currently have modules for my user on ffluxlab which I intend to publish for all users once I am happy that they're stable and get the required permissions. Until then, you can download Anaconda3 using this [link](https://repo.anaconda.com/archive/Anaconda3-2019.10-Linux-x86_64.sh). For setting up the other necessary applications, ask [me](https://github.com/MattBurn) and I will help to get you started.
#### All Machines
Other than Anaconda and Gaussian, a copy of AIMAll, DL FFLUX and FEREBUS is required. AIMAll can be downloaded from [here](http://aim.tkgristmill.com/), again ask [me](https://github.com/MattBurn) about how to download and install AIMAll. AIMAll must be installed in your home directory `~/AIMAll`. Versions of FEREBUS, FEREBUS.py and DL FFLUX are included in the `PROGRAMS` directory in this repository. These binaries were compiled on CSF and so are only guaranteed to work there, for other machines/versions, you will be required to compile your own and place them in this directory under the same name.
### Dependencies
---
Some programs used by ICHOR have additional dependencies which are listed below. When first downloading and copying these programs to your machine of choice, make sure that the binaries have running permisions by uising `chmod`, for example:
```
chmod 777 PROGRAMS/DLPOLY.Z
```
#### ICHOR
ICHOR has been designed with as few dependencies as possible and the dependencies that are there should be available to most machines with anaconda. A list of the dependencies can be found at the top of ICHOR.py under the comment `# Required imports`.
* numpy (required)
* scipy (required)
* tqdm (required)
* paramiko (optional/experimental)
#### FEREBUS
To compile FEREBUS, an intel mpi compiler is required along with the ucx library and intel nag library. Changing where FEREBUS is compiled, the compiler and library versions may require changes of the `Makefile`. The specific compilers and libraries used to compile the verion in `PROGRAMS` are as follows:
* Intel MPI Compiler 2018.3.022
* Intel Fortran Compiler 2018.3.022
* Intel NAG Fortran Mark 23
* UCX 1.5.1
#### FEREBUS.py
FEREBUS.py is a reimplementation of FEREBUS in python (as the name suggests) the repository and documentation of which can be found [here](https://github.com/popelier-group/pyFEREBUS). This repository contains a detailed explanation of all the dependencies required to run FEREBUS.py.
* george = 0.3.1
* numpy = 1.16.3
* pandas = 0.24.2
* pybind11 = 2.2.4
* python-dateutil = 2.8.0
* pytz  = 2019.1
* scikit-learn = 0.20.3
* scipy = 1.2.1
* six = 1.12.0
#### DL FFLUX
The version of DL FFLUX used by ICHOR is compiled using the gcc compiler. The specific version of which is not of great concern but the more recent the better. The version in the `PROGRAMS` directory was compiled with gcc 8.2.0.
## Running ICHOR
---
Running ICHOR is as simple as running any python program:
```
python ICHOR.py
```
A list of command line options can be viewed by using the `-h` flag when running ICHOR. Global variables can be set and changed using a config file, by default this file is `config.properties` however this can be changed by setting the `-c` flag when running ICHOR. A full list of global variables can be found under the `Globals` comment at the top of the ICHOR script.
### Example config.properties
---
ICHOR can read [.properties](https://en.wikipedia.org/wiki/.properties) and [.yaml](https://en.wikipedia.org/wiki/YAML) filetypes, an example of a `config.properties` for water can be seen below:
```
SYSTEM_NAME=WATER
MAX_ITERATION=15
POINTS_PER_ITERATION=3

ALF=[[1,2,3],[2,1,3],[3,1,2]]

METHOD=B3LYP
BASIS_SET=6-31+g(d,p)
```
There are no required fields to run ICHOR, it is reccomended you set a `SYSTEM_NAME` variable so that when looking through files, it is easy to see what system you're working with. A list of default values are the same as the values set at the top of the ICHOR script. As you can see, no quotes are required for strings, and to make a list (`ALF`), python syntax is used.
### Menu
---
![Main-Menu](doc/img/main-menu.png?raw=true "Main Menu")

ICHOR has a problem finder implemented that looks for potential problems when initialising the program. If the problem is expected and not out of the ordinary, an option to disbale displaying these problems will soon be added.

Choosing an option is as simple as selecting the label and pressing enter, some options have sub menus which work in the same way.

### Training Set
---
![Training-Set-Menu](doc/img/training-set-menu.PNG?raw=true "Training Set Menu")

The training set menu `[1]` is used to work with the training points for your model. To initialise the training set, create a `TRAINING_SET` directory and put the points you want to add to the training set as `.gjf` form in this directory.

Once the GJFs are in the `TRAINING_SET` directory, option `[1]` will submit these GJFs to Gaussian to get `.wfn` files, option `[2]` will take these WFNs and submit them to AIMAll to get `.int` files, option `[3]` will take these INT files and create Gaussian Process Regression (GPR) models using FEREBUS. These models will be located in `FEREBUS/MODELS`.
### Models
![Model-Menu](doc/img/model-menu.PNG?raw=true "Model Menu")

Option `[3]` of the training set menu brings you to a model menu. In this menu you can choose which output features you want to use to create your GPR models. Option `[1]` creates IQA models and option `[2]` creates a model for each of the 25 multipole moments used in DL FFLUX.
### Sample Pool
---
![Sample-Set-Menu](doc/img/sample-pool-menu.PNG?raw=true "Sample pool Menu")

The sample pool is used by adaptive sampling as a set of points to choose from to improve the training set. The sample pool menu functions in the same way as the training set menu without the option to form models from this set. To setup the sample pool, place your points in `.gjf` from into a directory with the name `SAMPLE_POOL`.
### Adaptive Sampling
---
The main purpose of ICHOR is to make adaptive sampling of GOR models easy. It is possible to run adaptive sampling manually by repeating the steps:
* `[1] [1]`
    * Run Gaussian on Training GJFs
* `[1] [2]`
    * Run AIMAll on Training WFNs
* `[1] [3] [1]`
    * Make IQA GPR models
* `[3]`
    * Run Adaptive sampling using GPR models and sample pool then add best points to the training set

* Repeat

Alternatively, once you have placed the training set GJFs into the `TRAINING_SET` directory and the sample pool GJFs into the `SAMPLE_POOL` directory, simply using the option `[r]` will automate the adaptive sampling process.

This Auto-Run is controlled using the two values `MAX_ITERATION` and `POINTS_PER_ITERATION` in the config file. `MAX_ITERATION` tells ICHOR how many times to repeat the adaptive sampling process and `POINTS_PER_ITERATION` tells ICHOR how many points to add from the sample pool to the training set each iteration.

For example if I start off with 50 training points and add 10 `POINTS_PER_ITERATION` for 10 `MAX_ITERATION`, I will add 100 points (10x10) to my training set and end up with 150 training points.

A log of all the models produced during the adaptive sampling run can be found in the `LOG` directory, each model will have its own directory under the naming convention of `LOG/SYSTEM_NAME####` where `SYSTEM_NAME` is the same as the `SYSTEM_NAME` specified in the config file and `####` is the number of training points in that model.
