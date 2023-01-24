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

try:
    from docker_image import reference

    HAS_DOCKER_IMAGE = True
except ImportError:
    HAS_DOCKER_IMAGE = False

DOCUMENTATION = """
  name: docker_image
  short_description: Parse a Docker image reference
  version_added: 0.13.0
  description:
    - Parse a Docker image and return different parts of the reference
    - This lookup module requires "docker-image-py" to be installed on the
      Ansible controller.
  options:
    _input:
      type: string
      required: true
      description:
          - Docker image reference to parse
    part:
      type: string
      default: 'ref'
      options: [name, ref, tag, domain, path]
      required: true
      description:
        - Part of the Docker image reference to return
    registry:
      type: string
      required: false
      description:
        - Override the registry in the Docker image reference
  author:
    - Mohammed Naser <mnaser@vexxhost.com>
"""

EXAMPLES = """
  - name: Generate a Docker image reference
    ansible.builtin.debug:
      msg: "{{ 'docker.io/library/memcached:1.6.3' | vexxhost.atmosphere.docker_image('name') }}"
"""

RETURN = """
  _value:
    description: The part of the Docker image reference
    type: string
"""


def docker_image(value, part="ref", registry=None):
    if not is_string(value):
        raise AnsibleFilterError(
            "Invalid value type (%s) for docker_image (%r)" % (type(value), value)
        )

    if not HAS_DOCKER_IMAGE:
        raise AnsibleFilterError(
            "Failed to import docker-image-py module, ensure it is installed on the controller"
        )

    def _lookup_part(ref, part):
        if part == "ref":
            return ref.string()
        if part == "name":
            return ref["name"]
        if part == "tag":
            return ref["tag"]
        if part == "domain":
            return ref.repository["domain"]
        if part == "path":
            return ref.repository["path"]

    ref = reference.Reference.parse(value)
    if not registry:
        return _lookup_part(ref, part)

    # NOTE(mnaser): We re-write the name of a few images to make sense of them
    #               in the context of the override registry.
    ref_name = ref.repository["path"].split("/")[-1]
    if value == "skopeo":
        ref_name = "skopeo-stable"

    # NOTE(mnaser): Since the attributes inside of reference.Reference are not
    #               determined during parse time, we need to re-parse the
    #               string to get the correct attributes.
    ref["name"] = "{}/{}".format(registry, ref_name)
    ref = reference.Reference.parse(ref.string())

    return _lookup_part(ref, part)


class FilterModule(object):
    def filters(self):
        return {"docker_image": docker_image}
