# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sys
from pathlib import Path

import builtins
builtins.__sphinx_build__ = True

sys.path.append(Path("../../ichor_cli/ichor/"))
sys.path.append(Path("../../ichor_core/ichor/"))
sys.path.append(Path("../../ichor_hpc/ichor/"))


project = 'ichor'
copyright = '2024, Yulian Manchev'
author = 'Yulian Manchev, Matthew Burn'
release = '4.0.2'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc", "sphinx_rtd_theme", "nbsphinx",
              "sphinx.ext.napoleon", "sphinx.ext.mathjax", "myst_parser"]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']

add_module_names = False

# executing notebooks takes a while
nbsphinx_execute = 'never'
