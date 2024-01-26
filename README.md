# ICHOR
## Machine Learning Suite for the Popelier Group

[![GitHub release](https://img.shields.io/badge/release-v2.1-blue)](https://github.com/popelier-group/ICHOR/releases/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Website popelier-group.herokuapp.com](https://img.shields.io/website-up-down-green-red/http/shields.io.svg)](https://popelier-group.herokuapp.com/docs/ichor/ichor/)

ICHOR is a Python package used to simplify computational chemistry programs and aid with machine learning force field development. The idea behind ICHOR is to abstract away the gritty details of running and linking between programs on High-Performance Computing (HPC) clusters. If you would like to request missing features or run into a bug, don't hesitate to create an [issue](https://github.com/popelier-group/ICHOR/issues).

## Getting Started
---
The namespace package `ichor` is divided into three parts, `ichor-core`, `ichor-hpc`, and `ichor-cli`. The `ichor-core` sub package contains classes and functions which make it easy to read relevant file and analyze outputs of jobs. The `ichor-hpc` package is used to submit jobs on CSF3, CSF4, and FFLUXLAB. The `ichor-cli` is a command line interface, providing easy access to the most common tools that a user might need to make machine learning models. To get started, only install the `ichor-core` and `ichor-hpc` subpackages (the `hpc` subpackage is only needed when submitting jobs on CSFs and FFLUXLAB, so you do not need to install it when working locally on your machine.)

** You will need to create a `ichor_config.yaml` for configuration settings, see the documentation for examples. **

## Documentation

**The documentation can also be found online [here](https://studious-adventure-rr4kzlv.pages.github.io/)**. You will need to be logged in as a member of Popelier Group Organization to access it, note that this will change when the code is made public.
