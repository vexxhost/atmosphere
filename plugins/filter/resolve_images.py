# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.errors import AnsibleFilterError
from ansible_collections.vexxhost.atmosphere.plugins.module_utils.release_manifest import (
    ReleaseManifestError,
)
from ansible_collections.vexxhost.atmosphere.plugins.module_utils.release_manifest import (
    resolve_images as _resolve_images,
)

DOCUMENTATION = """
  name: resolve_images
  short_description: Apply the image prefix and mirror rules to image references
  version_added: 1.0.0
  description:
    - Resolve canonical image references (for example from a release
      manifest) to the references a deployment pulls, applying
      C(atmosphere_image_mirrors) rules and C(atmosphere_image_prefix).
    - The most specific rule matching an image repository wins; images that
      no rule matches get the image prefix.
  options:
    _input:
      description: Mapping of image keys to image references.
      type: dict
      required: true
    prefix:
      description: The C(atmosphere_image_prefix) value.
      type: str
      default: ""
    mirrors:
      description: The C(atmosphere_image_mirrors) rules, each with a C(source) and a C(mirror).
      type: list
      elements: dict
      default: []
    strip_prefix:
      description:
        - Remove the prefix from the input first, for references that
          already include it (the source image list in the defaults role).
      type: bool
      default: false
  author:
    - VEXXHOST, Inc.
"""

EXAMPLES = """
- name: Resolve release images for a Harbor proxy
  ansible.builtin.debug:
    msg: >-
      {{ manifest_images | vexxhost.atmosphere.resolve_images(
           prefix='harbor.example.com/',
           mirrors=[{'source': 'docker.io', 'mirror': 'harbor.example.com/dockerhub-proxy'}]) }}
"""

RETURN = """
  _value:
    description: Mapping of image keys to the references to deploy.
    type: dict
"""


def resolve_images(images, prefix="", mirrors=None, strip_prefix=False):
    try:
        return _resolve_images(
            images, prefix=prefix, mirrors=mirrors or [], strip_prefix=strip_prefix
        )
    except ReleaseManifestError as e:
        raise AnsibleFilterError(str(e))


class FilterModule(object):
    def filters(self):
        return {"resolve_images": resolve_images}
