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

from ansible.errors import AnsibleFilterError
from ansible.module_utils.common.collections import is_string

import uuid

DOCUMENTATION = """
  name: is_uuid_like
  short_description: Determine if the string is a UUID
  version_added: 1.0.1
  description:
    - Determine if the string is a UUID
  options:
    _input:
      type: string
      required: true
      description:
          - String to check
  author:
    - Mohammed Naser <mnaser@vexxhost.com>
"""

EXAMPLES = """
  - name: Determine if a string is a UUID
    ansible.builtin.debug:
      msg: "{{ 'a3b8f2bc-9cd1-11d1-80b4-00c04fd430c8' | is_uuid_like }}"
"""

RETURN = """
  _value:
    description: True if the string is a UUID, False otherwise
    type: string
"""


def _format_uuid_string(string):
    return (
        string.replace("urn:", "")
        .replace("uuid:", "")
        .strip("{}")
        .replace("-", "")
        .lower()
    )


def is_uuid_like(val):
    if not is_string(val):
        raise AnsibleFilterError(
            "Invalid value type (%s) for is_uuid_like (%r)" % (type(val), val)
        )

    try:
        return str(uuid.UUID(val)).replace("-", "") == _format_uuid_string(val)
    except (TypeError, ValueError, AttributeError):
        return False


class FilterModule(object):
    def filters(self):
        return {"is_uuid_like": is_uuid_like}
