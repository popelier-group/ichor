.. ichor documentation master file, created by
   sphinx-quickstart on Sat Jun 17 19:23:10 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ichor's documentation!
=================================

Introduction
************

The :code:`ichor` package is a namespace package that contains three packages:
:code:`ichor.core`, :code:`ichor.hpc`, and :code:`ichor.cli`. The :code:`ichor.core` packages
contains mostly file management and analysis tools for the different types of files
that must be read (from Gaussian, AIMAll, etc.). The :code:`ichor.hpc` package
contains code allows a user to submit jobs on compute clusters (SGE and SLURM).
The :code:`ichor.cli` packages is a menu system that allows a user to do the most
common tasks without having to write individual scripts.

.. toctree::
   :maxdepth: 1
   :caption: ichor.core

   ichor_core_examples_toc
   ichor_core/ichor.core

.. toctree::
   :maxdepth: 1
   :caption: Subpackages:

   ichor_hpc/ichor.hpc
   ichor_cli/ichor.cli

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
