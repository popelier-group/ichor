# ICHOR
## Machine Learning Suite for the Popelier Group

[![GitHub release](https://img.shields.io/badge/release-v2.1-blue)](https://github.com/popelier-group/ICHOR/releases/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Website popelier-group.herokuapp.com](https://img.shields.io/website-up-down-green-red/http/shields.io.svg)](https://popelier-group.herokuapp.com/docs/ichor/ichor/)

ICHOR is a program written in python that is used to parse inputs and outputs of various programs (Gaussian, AIMALL, DL_FFLUX, AMBER, CP2K, etc.), and run programs  on High Performance Compute (HPC) clusters. It also contains many critical tools for machine learning model development as well as data analysis. The idea behind ICHOR is to abstract away the gritty details of running and linking between the programs you use while performing these tasks so if there are features you think are missing or problems that can be made simpler, don't hesitate to create an [issue](https://github.com/popelier-group/ICHOR/issues) if there is a problem with the code.

![ICHOR Diagram](doc/img/ICHOR-diagram.png?raw=true "ICHOR Diagram")

## Getting Started
---
The namespace package `ichor` is divided into three parts, `ichor-core`, `ichor-hpc`, and `ichor-cli`. The `ichor-core` sub package contains classes and functions which make it easy to read relevant file and analyze outputs of jobs. The `ichor-hpc` package is used to submit jobs on CSF3, CSF4, and FFLUXLAB. The `ichor-cli` is a command line interface, providing easy access to the most common tools that a user might need to make machine learning models. To get started, only install the `ichor-core` and `ichor-hpc` subpackages (the `hpc` subpackage is only needed when submitting jobs on CSFs and FFLUXLAB, so you do not need to install it when working locally on your machine.)

## Documentation

Look inside the ``docs/build`` directory for documentation. This documentation will be available online once the code is open sourced. This is where you will find installation instructions, guides, and other useful materials.

## Useful Links

* Anaconda3 [link](https://www.anaconda.com/distribution/#download-section)
* Gaussian  [link](https://gaussian.com/glossary/g09/)
* AIMAll    [link](http://aim.tkgristmill.com/)
* FEREBUS   [F90](https://github.com/popelier-group/FEREBUS) [Py](https://github.com/popelier-group/pyFEREBUS)
* DL FFLUX  [source](https://github.com/popelier-group/DL_POLY)
