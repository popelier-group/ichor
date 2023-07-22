# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sys
from pathlib import Path

sys.path.append(Path("../../ichor_cli_subpackage/ichor/"))
sys.path.append(Path("../../ichor_core_subpackage/ichor/"))
sys.path.append(Path("../../ichor_hpc_subpackage/ichor/"))


project = 'ichor'
copyright = '2023, Yulian Manchev'
author = 'Yulian Manchev, Matthew Burn'
release = '3.1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = ["sphinx.ext.autodoc", "sphinx_rtd_theme", "nbsphinx", "sphinx.ext.napoleon", "sphinx.ext.mathjax"]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ['_static']

add_module_names = False
