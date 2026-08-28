# ichor
---

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Run Tests](https://github.com/popelier-group/ICHOR/actions/workflows/run_tests.yml/badge.svg)](https://github.com/popelier-group/ICHOR/actions/workflows/run_tests.yml)
![Release](https://img.shields.io/github/v/release/popelier-group/ICHOR?sort=semver)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Documentation Status](https://readthedocs.org/projects/ichor/badge/?version=latest)](https://ichor.readthedocs.io/en/latest/?badge=latest)

`ichor` is a Python package used to simplify data management from computational chemistry programs and aid with machine learning force field development. If you would like to request missing features or run into a bug, don't hesitate to create an [issue](https://github.com/popelier-group/ICHOR/issues).

Here is a list of things that the package is intended to do:

1. provide interfaces to any computational chemistry software to allow for easy switching between similar software and results comparison.
2. implement flexible data structures to allow for data management of hundreds of thousands of calculations from multiple programs.
3. integrate common database formats for efficient data storage, sharing, and post-processing
4. provide interfaces to workload managers on compute clusters to automate job submission
5. collate tools for machine learning dataset and model analysis, as well as molecular dynamics simulation benchmarking

Realistically, the file management portion of `ichor` (as well as the workload manager integration) is very general, so it can be used for any type of data that might not even be computational chemistry related. However, the focus of the source code itself is on computational chemistry and machine learning force field development.

## Citing Us

If you use `ichor`, please cite the following two papers:

- [Y. T. Manchev, M. J. Burn, P. L. A. Popelier, J. Comput. Chem.2024, 45(32), 2912.](https://doi.org/10.1002/jcc.27477)
- [M. J. Burn, P. L. A. Popelier, Materials Advances.2022, 3(23), 8729.](https://doi.org/10.1039/D2MA00673A)

## Documentation

Documentation of all three packages, including examples, can be found [here](https://ichor.readthedocs.io/en/latest/).

## Installation
---

ichor needs Python 3.10 or newer. From a clone of this repository:

```
python3 -m pip install -e ichor_core -e ichor_hpc -e ichor_cli
ichor-config-init
```

All three packages go in one command: they depend on each other and are not on PyPI, so pip can only resolve them if it is given all three at once. `ichor-config-init` writes an example config to `~/.config/ichor/config.yaml`, which you then edit for the cluster you are on.

The ASE optimisation and metadynamics jobs run in a separate conda environment, because `xtb` and the PLUMED Python wrappers are only built for current Python versions on conda-forge. If you use those jobs, also run

```
conda env create -f environment.yml
```

and point the `software.python` block of your config file at it. See the [installation documentation](https://ichor.readthedocs.io/en/latest/installation.html) for the full walkthrough on a compute cluster.

## Getting Started
---
The namespace package `ichor` is divided into three parts, `ichor.core`, `ichor.hpc`, and `ichor.cli`.

### `ichor.core`
The `ichor.core` package contains classes and functions which make it easy to handle a very large number of files, perform many calculations with the outputs contained in the file, as well as aid with machine learning force field development.

### `ichor.hpc`
The `ichor.hpc` package is used to submit jobs on compute clusters (SGE/SLURM).

### `ichor.cli`
The `ichor.cli` package provides a simple to use command line interface (CLI), providing an easy access to access the most commonly used tools from ichor.

### Configuration

`ichor.hpc` and `ichor.cli` need a config file describing the HPC clusters you run on: which modules to load, where each program lives, and what parallel environments are available. After installing, run

```
ichor-config-init
```

which writes an example config to `~/.config/ichor/config.yaml` for you to edit. If you already have an `ichor_config.yaml` in your home directory from an older version of ichor, the same command moves it to the new location. Refer to the documentation for what goes in it.

## Contributing

Contributions are very welcome! More information on how to correctly contribute can be found in the [CONTRIBUTING.md](CONTRIBUTING.md) file.

## License

`ichor` is [MIT Licensed.](https://github.com/popelier-group/ichor/blob/main/LICENSE)
