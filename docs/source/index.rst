.. ichor documentation master file, created by
   sphinx-quickstart on Sat Jun 17 19:23:10 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ichor's documentation!
=================================

Introduction
************

:code:`ichor` is a Python package used to simplify data management from computational chemistry programs and aid
with machine learning force field development.

Here is a list of things that the package is intended to do:

- provide interfaces to any computational chemistry software to allow for easy switching between similar software and results comparison.
- implement flexible data structures to allow for data management of hundreds of thousands of calculations from multiple programs.
- integrate common database formats for efficient data storage, sharing, and post-processing
- provide interfaces to workload managers on compute clusters to automate job submission
- collate tools for machine learning dataset and model analysis, as well as molecular dynamics simulation benchmarking

Realistically, the file management portion of ichor (as well as the workload manager integration) is very general, so it can be used for any type of data that might not even be computational chemistry related. However, the focus of the source code itself is on computational chemistry and machine learning force field development.

The :code:`ichor` package is a namespace package that contains three packages:
:code:`ichor.core`, :code:`ichor.hpc`, and :code:`ichor.cli`. The :code:`ichor.core` packages
contains mostly file management and analysis tools for the different types of files
that must be read (from Gaussian, AIMAll, etc.). The :code:`ichor.hpc` package
contains code allows a user to submit jobs on compute clusters (SGE and SLURM).
The :code:`ichor.cli` packages is a menu system that allows a user to do the most
common tasks without having to write individual scripts.

Below are examples of how to use ``ichor``.

.. toctree::
   :maxdepth: 1

   installation
   ichor_config_setup
   ichor_core_examples_toc
   ichor_hpc_examples_toc
   ichor_cli_examples_toc

.. toctree::
   :maxdepth: 1
   :caption: full documentation of source code

   ichor_core/ichor.core
   ichor_hpc/ichor.hpc
   ichor_cli/ichor.cli

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
