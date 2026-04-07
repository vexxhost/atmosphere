# Copyright (c) 2023 VEXXHOST, Inc.
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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import json
import os

from ansible.errors import AnsibleLookupError
from ansible.plugins.lookup import LookupBase

try:
    import rjsonnet

    HAS_RJSONNET = True
except ImportError:
    HAS_RJSONNET = False


DOCUMENTATION = """
  name: jsonnet
  author: Mohammed Naser (@mnaser) <mnaser@vexxhost.com>
  version_added: "0.13"
  short_description: Compile jsonnet file
  description:
    - This lookup returns the compiled jsonnet file
  options:
    _terms:
      description: jsonnet file path
      required: True
"""


def import_callback(base, rel):
    """
    :param base: The directory containing the code that did the import.
    :param rel: The path imported by the code.
    """
    path = os.path.join(base, rel)
    with open(path, "r") as f:
        return path, f.read()


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        if not HAS_RJSONNET:
            raise AnsibleLookupError("rjsonnet is required for this lookup")

        ret = []

        for term in terms:
            file = self.find_file_in_search_path(variables, "files", term)
            if not file:
                raise AnsibleLookupError("Could not find file %s" % term)

            def import_callback(base, rel):
                """
                :param base: The directory containing the code that did the import.
                :param rel: The path imported by the code.
                """
                path = self.find_file_in_search_path(variables, base, rel)
                with open(path, "r") as f:
                    return path, f.read()

            compiled_string = rjsonnet.evaluate_file(
                file, import_callback=import_callback
            )
            compiled = json.loads(compiled_string)
            ret.append(compiled)

        return ret
