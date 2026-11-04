# Copyright (c) 2026 VEXXHOST, Inc.
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
from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.common.collections import is_string

DOCUMENTATION = """
  name: ssh_public_key
  short_description: Get the OpenSSH public key of a private key
  version_added: 6.0.0
  description:
    - Return the public key of an unencrypted SSH private key, in the
      C(<type> <base64>) format used by C(authorized_keys), without a comment.
    - Accepts private keys in OpenSSH or PEM format.
  options:
    _input:
      type: string
      required: true
      description:
        - The private key contents
  author:
    - Mohammed Naser <mnaser@vexxhost.com>
"""

EXAMPLES = """
  - name: Print the public key of an SSH private key
    ansible.builtin.debug:
      msg: "{{ lookup('file', 'id_ed25519') | vexxhost.atmosphere.ssh_public_key }}"
"""

RETURN = """
  _value:
    description: The OpenSSH public key
    type: string
"""


def ssh_public_key(value):
    if not is_string(value):
        raise AnsibleFilterError(
            "Invalid value type (%s) for ssh_public_key" % type(value)
        )

    try:
        from cryptography.hazmat.primitives import serialization
    except ImportError as e:
        raise AnsibleFilterError("ssh_public_key requires cryptography: %s" % e)

    data = to_bytes(value.strip() + "\n")
    try:
        if b"-----BEGIN OPENSSH PRIVATE KEY-----" in data:
            key = serialization.load_ssh_private_key(data, password=None)
        else:
            key = serialization.load_pem_private_key(data, password=None)
    except (ValueError, TypeError) as e:
        # NOTE: Never include the input here, it is a private key.
        raise AnsibleFilterError("Unable to load SSH private key: %s" % e)

    return to_text(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.OpenSSH,
            format=serialization.PublicFormat.OpenSSH,
        )
    )


class FilterModule(object):
    def filters(self):
        return {"ssh_public_key": ssh_public_key}
