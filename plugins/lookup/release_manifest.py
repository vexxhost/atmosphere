# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os

from ansible.errors import AnsibleLookupError
from ansible.plugins.lookup import LookupBase
from ansible_collections.vexxhost.atmosphere.plugins.module_utils.release_manifest import (
    ReleaseManifestError,
    images_for_kubernetes_version,
    load_manifest,
    resolve_location,
)

DOCUMENTATION = """
  name: release_manifest
  short_description: Read the images of an Atmosphere release manifest
  version_added: 1.0.0
  description:
    - Returns the digest-pinned images of an Atmosphere release manifest, read
      from a local file or downloaded from an OCI registry.
    - Manifests are cached for the lifetime of the Ansible process.
  options:
    _terms:
      description:
        - Path to a release manifest file, or an OCI reference such as
          C(ghcr.io/vexxhost/atmosphere-release:v7.8.1).
      required: true
    kubernetes_version:
      description:
        - The Kubernetes version being deployed. If it differs from the
          version the manifest pins, the Kubernetes control plane images use
          the tag for this version instead.
      type: str
    prefix:
      description:
        - The C(atmosphere_image_prefix) value. It is applied to an OCI
          reference like to every image, unless a mirror rule matches it.
      type: str
      default: ""
    mirrors:
      description: The C(atmosphere_image_mirrors) rules, applied to an OCI reference.
      type: list
      elements: dict
      default: []
    ca_file:
      description:
        - A CA certificate file to trust, in addition to the system
          certificates, when downloading the manifest from a registry.
      type: str
    plain_http:
      description: Use HTTP instead of HTTPS to reach the registry.
      type: bool
      default: false
  author:
    - VEXXHOST, Inc.
"""

EXAMPLES = """
- name: Show the images of a release
  ansible.builtin.debug:
    msg: "{{ query('vexxhost.atmosphere.release_manifest', 'ghcr.io/vexxhost/atmosphere-release:v7.8.1') | first }}"
"""

RETURN = """
  _list:
    description: A list with one mapping of image keys to image references.
    type: list
    elements: dict
"""

_CACHE = {}


def _cache_key(location):
    if os.path.isfile(location):
        return (location, os.path.getmtime(location))
    return (location, None)


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        self.set_options(var_options=variables, direct=kwargs)
        kubernetes_version = self.get_option("kubernetes_version")
        plain_http = self.get_option("plain_http")
        prefix = self.get_option("prefix") or ""
        mirrors = self.get_option("mirrors") or []
        ca_file = self.get_option("ca_file") or None

        results = []
        for term in terms:
            location = str(term).strip()
            if not location:
                raise AnsibleLookupError("a release manifest location is required")

            try:
                location = resolve_location(location, prefix=prefix, mirrors=mirrors)
                key = _cache_key(location) + (plain_http, ca_file)
                if key not in _CACHE:
                    _CACHE[key] = load_manifest(
                        location, plain_http=plain_http, ca_file=ca_file
                    )
                results.append(
                    images_for_kubernetes_version(_CACHE[key], kubernetes_version)
                )
            except ReleaseManifestError as e:
                raise AnsibleLookupError("release manifest %s: %s" % (location, e))
            except (IOError, OSError) as e:
                raise AnsibleLookupError("release manifest %s: %s" % (location, e))

        return results
