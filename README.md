# ichor

[![GitHub release](https://img.shields.io/badge/release-v2.1-blue)](https://github.com/popelier-group/ICHOR/releases/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Website popelier-group.herokuapp.com](https://img.shields.io/website-up-down-green-red/http/shields.io.svg)](https://studious-adventure-rr4kzlv.pages.github.io/)

**ichor** is a Python package used to simplify computational chemistry programs and aid with machine learning force field development. If you would like to request missing features or run into a bug, don't hesitate to create an [issue](https://github.com/popelier-group/ICHOR/issues).

## Getting Started
---
The namespace package `ichor` is divided into three parts, `ichor-core`, `ichor-hpc`, and `ichor-cli`. The `ichor-core` sub package contains classes and functions which make it easy to read relevant file and analyze outputs of jobs. The `ichor-hpc` package is used to submit jobs on compute clusters (only SGE/SLURM supported at the moment). The `ichor-cli` is a command line interface, providing easy access to the most common tools from ichor.

**You will need to create a `ichor_config.yaml` in your home directory for configuration settings, see the documentation for examples.**

## Documentation

**The documentation can also be found online [here](https://studious-adventure-rr4kzlv.pages.github.io/)**. You will need to be logged in as a member of Popelier Group Organization to access it, note that this will change when the code is made public.
