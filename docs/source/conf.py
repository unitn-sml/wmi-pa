# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath("../src/"))  # Source code dir relative to this file

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "wmpy"
copyright = "2025, the wmpy team"
author = "the wmpy team"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration


extensions = [
    "sphinx.ext.napoleon",  # more readable docstrings
    "sphinx.ext.autosummary",  # automatic recursion in src
    "sphinx.ext.autodoc",  # Core Sphinx library for auto html doc generation from docstrings
    "sphinx.ext.autosummary",  # Create neat summary tables for modules/classes/methods etc
    "sphinx.ext.intersphinx",  # Link to other project's documentation (see mapping below)
    "sphinx.ext.viewcode",  # Add a link to the Python source code for classes, functions etc.
    "sphinx_autodoc_typehints",  # Automatically document param types (less noise in class signature)
    "nbsphinx",  # Integrate Jupyter Notebooks and Sphinx
    "IPython.sphinxext.ipython_console_highlighting",
    "myst_parser", # For importing Markdown
]

# Mappings for sphinx.ext.intersphinx. Projects have to have Sphinx-generated doc! (.inv file)
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
}

napoleon_google_docstring = True  # using Google style (swap for numpy style)
napoleon_numpy_docstring = False

autosummary_generate = True  # Turn on sphinx.ext.autosummary

autoclass_content = "both"  # Add __init__ doc (ie. params) to class summaries

html_show_sourcelink = (
    False  # Remove 'view source code' from top of page (for html, not python)
)

autodoc_inherit_docstrings = True  # If no docstring, inherit from base class

autodoc_mock_imports = ["wmpy.cli"]  # Do not create API reference for the CLI

set_type_checking_flag = True  # Enable 'expensive' imports for sphinx_autodoc_typehints

nbsphinx_allow_errors = True  # Continue through Jupyter errors

# autodoc_typehints = "description" # Sphinx-native method. Not as good as sphinx_autodoc_typehints

add_module_names = False  # Remove namespaces from class/method signatures

templates_path = ["_templates"]
exclude_patterns = [""]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# Readthedocs theme
# on_rtd is whether on readthedocs.org, this line of code grabbed from docs.readthedocs.org...
on_rtd = os.environ.get("READTHEDOCS", None) == "True"
if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme

    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_css_files = ["readthedocs-custom.css"]  # Override some CSS settings

html_static_path = ["_static"]
