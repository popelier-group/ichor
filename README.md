# ichor
---

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Run Tests](https://github.com/popelier-group/ICHOR/actions/workflows/run_tests.yml/badge.svg)](https://github.com/popelier-group/ICHOR/actions/workflows/run_tests.yml)
[![GitHub release](https://img.shields.io/badge/release-v4.0.1-blue)](https://github.com/popelier-group/ICHOR/releases/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![docs](https://img.shields.io/website-up-down-green-red/http/shields.io.svg)](https://studious-adventure-rr4kzlv.pages.github.io/)

`ichor` is a Python package used to simplify computational chemistry programs and aid with machine learning force field development. If you would like to request missing features or run into a bug, don't hesitate to create an [issue](https://github.com/popelier-group/ICHOR/issues).

Here is a list of things that the package is intended to do:

1. provide interfaces to any computational chemistry software to allow for easy switching between similar software and results comparison.
2. implement flexible data structures to allow for data management of hundreds of thousands of calculations from multiple programs.
3. integrate common database formats for efficient data storage, sharing, and post-processing
4. provide interfaces to workload managers on compute clusters to automate job submission
5. collate tools for machine learning dataset and model analysis, as well as molecular dynamics simulation benchmarking

Realistically, the file management part of `ichor` is very general, so it can be used to manage any type of data that might not be computational chemistry related. However, the focus of the source code itself is on computational chemistry data.

## Getting Started
---
The namespace package `ichor` is divided into three parts, `ichor-core`, `ichor-hpc`, and `ichor-cli`. The `ichor-core` sub package contains classes and functions which make it easy to read relevant file and analyze outputs of jobs. The `ichor-hpc` package is used to submit jobs on compute clusters (only SGE/SLURM supported at the moment). The `ichor-cli` is a command line interface, providing easy access to the most common tools from ichor.

**You will need to create a `ichor_config.yaml` in your home directory for configuration settings, see the documentation for examples.**

## Documentation

**The documentation can also be found online [here](https://studious-adventure-rr4kzlv.pages.github.io/)**. You will need to be logged in as a member of Popelier Group Organization to access it, note that this will change when the code is made public.

## Contributing

Contributions are very welcome! More information on how to correctly contribute can be found in the [CONTRIBUTING.md](CONTRIBUTING.md) file.
