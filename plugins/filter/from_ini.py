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

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from functools import partial

from ansible.errors import AnsibleFilterError
from ansible.module_utils._text import to_text
from ansible.module_utils.common.collections import is_string
from ansible.module_utils.six.moves import configparser

DOCUMENTATION = """
  name: from_ini
  short_description: Parse an INI file
  version_added: 1.0.0
  description:
    - Parse an INI file and return a dictionary
  options:
    _input:
      type: string
      required: true
      description:
          - The INI file contents to parse
  author:
    - Mohammed Naser <mnaser@vexxhost.com>
"""

EXAMPLES = """
  - name: Parse an INI file
    ansible.builtin.debug:
      msg: "{{ lookup('file', 'config.ini') | from_ini }}"
"""

RETURN = """
  _value:
    description: The parsed INI file
    type: dict
"""


def from_ini(value):
    if not is_string(value):
        raise AnsibleFilterError(
            "Invalid value type (%s) for from_ini (%r)" % (type(value), value)
        )

    parser = configparser.RawConfigParser()
    parser.optionxform = partial(to_text, errors="surrogate_or_strict")
    parser.read_string(value)

    data = {}

    def _parse_section(section):
        data = dict(section)
        data.pop("__name__", None)
        for opt, val in data.items():
            if val.isdigit():
                val = int(val)
            elif val.lower() in ("true", "false"):
                val = True if val.lower() == "true" else False
            elif val.lower() in ("none", "null"):
                val = None
            elif isinstance(val, str):
                val = val.strip('"')
            else:
                try:
                    val = float(val)
                except ValueError:
                    pass
            data[opt] = val

        return data

    data = dict(parser._sections)
    for k in data:
        data[k] = _parse_section(data[k])
    if parser._defaults:
        data["DEFAULT"] = _parse_section(parser._defaults)

    return data


class FilterModule(object):
    def filters(self):
        return {"from_ini": from_ini}
