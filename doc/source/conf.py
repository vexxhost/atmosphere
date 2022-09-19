# Copyright (c) 2022 VEXXHOST, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

import glob

# -- yaml2rst ----------------------------------------------------------------
import os
import pathlib

import yaml2rst
from yaml4rst.reformatter import YamlRstReformatter

for defaults_file in glob.glob("../../roles/*/defaults/main.yml"):
    role_name = defaults_file.split("/")[-3]

    YamlRstReformatter._HEADER_END_LINES = {
        "yaml4rst": [
            "# Default variables",
            "#    :local:",
            "# .. contents:: Sections",
            "# .. include:: includes/all.rst",
            "# .. include:: includes/role.rst",
            "# .. include:: ../../../includes/global.rst",
            "# -----------------",
        ],
    }

    reformatter = YamlRstReformatter(
        preset="yaml4rst",
        template_path=os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "_templates",
        ),
        config={
            "ansible_full_role_name": f"vexxhost.atmosphere.{role_name}",
            "ansible_role_name": role_name,
        },
    )
    reformatter.read_file(defaults_file)
    reformatter.reformat()
    reformatter.write_file(
        output_file=defaults_file,
        only_if_changed=True,
    )

    pathlib.Path(f"roles/{role_name}/defaults").mkdir(parents=True, exist_ok=True)

    rst_content = yaml2rst.convert_file(
        defaults_file,
        f"roles/{role_name}/defaults/main.rst",
        strip_regex=r"\s*(:?\[{3}|\]{3})\d?$",
        yaml_strip_regex=r"^\s{66,67}#\s\]{3}\d?$",
    )


# -- Project information -----------------------------------------------------

project = "Atmosphere"
copyright = "2022, VEXXHOST, Inc."
author = "VEXXHOST, Inc."


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "reno.sphinxext",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
