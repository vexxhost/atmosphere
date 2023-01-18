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

import os

import yaml
from ansible.errors import AnsibleFilterError

DOCUMENTATION = """
  name: openstack_helm_image_tags
  short_description: Generate list of image tags for an OpenStack Helm chart
  version_added: 0.13.0
  description:
    - Use an image manifest list to generate image tags for OpensStack Helm
  options:
    _input:
      type: dict
      required: true
      description:
          - Image manifest list
    chart:
      type: string
      required: true
      description:
        - OpenStack Helm chart name to generate image tags for
  author:
    - Mohammed Naser <mnaser@vexxhost.com>
"""

EXAMPLES = """
  - name: Generate image tags for Magnum OpenStack Helm chart
    ansible.builtin.debug:
      msg: "{{ atmosphere_images | community.general.openstack_helm_image_tags('magnum') }}"
"""

RETURN = """
  _value:
    description: Dictionary of image tags for the OpenStack Helm chart
    type: dict
"""

SKIP_LIST = [
    "image_repo_sync",
    "nova_wait_for_computes_init",
    "purge_test",
    "scripted_test",
    "test",
]


def openstack_helm_image_tags(value, chart):
    """Generate image tags for OpenStack Helm charts."""
    if not isinstance(value, dict):
        raise AnsibleFilterError("openstack_helm_image_tags expects a dictionary")

    # Start by parsing the `values.yaml` and exporting the tag list
    # for the chart
    values_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "charts",
        chart,
        "values.yaml",
    )

    with open(values_path) as fd:
        values = yaml.safe_load(fd)

    return {
        image: value[image]
        for image in values["images"]["tags"]
        if image not in SKIP_LIST
    }


class FilterModule(object):
    def filters(self):
        return {"openstack_helm_image_tags": openstack_helm_image_tags}
