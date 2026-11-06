# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import re

from ansible.errors import AnsibleFilterError

DOCUMENTATION = """
  name: multipath_unlisted_maps
  short_description: Find active multipath maps that a device allow-list would block
  version_added: 1.0.0
  description:
    - Parse C(multipath -ll) output and return the maps whose vendor and
      product match none of the allowed device entries.
    - Vendor and product patterns are searched like multipath-tools regular
      expressions. Maps whose WWID is explicitly excluded are ignored.
  options:
    _input:
      description: Output of C(multipath -ll).
      type: str
      required: true
    devices:
      description: Allowed device entries, each with C(vendor) and C(product) patterns.
      type: list
      elements: dict
      required: true
    excluded_wwids:
      description: WWIDs that are intentionally blacklisted.
      type: list
      elements: str
      default: []
  author:
    - VEXXHOST, Inc.
"""

EXAMPLES = """
- name: Show maps that would be blocked
  ansible.builtin.debug:
    msg: >-
      {{ multipath_output.stdout | vexxhost.atmosphere.multipath_unlisted_maps(
           [{'vendor': 'NETAPP', 'product': 'LUN.*'}]) }}
"""

RETURN = """
  _value:
    description: Descriptions of blocked maps, such as C(mpatha (3600...) PURE,FlashArray).
    type: list
    elements: str
"""

# Map header, for example "mpatha (3600a0980...) dm-0 NETAPP,LUN C-Mode" or
# "3600a0980... dm-0 NETAPP,LUN C-Mode" when the alias is the WWID.
_HEADER = re.compile(
    r"^(?P<name>\S+)\s+(?:\((?P<wwid>[^)]+)\)\s+)?dm-\d+\s+"
    r"(?P<vendor>[^,]*),(?P<product>.*?)\s*$"
)


def multipath_unlisted_maps(output, devices, excluded_wwids=None):
    excluded = set(excluded_wwids or [])
    try:
        patterns = [
            (re.compile(d["vendor"]), re.compile(d["product"])) for d in devices
        ]
    except (KeyError, TypeError, re.error) as e:
        raise AnsibleFilterError("invalid multipath device entry: %s" % e)

    blocked = []
    for line in (output or "").splitlines():
        match = _HEADER.match(line)
        if not match:
            continue
        name, wwid = match.group("name"), match.group("wwid") or match.group("name")
        if wwid in excluded:
            continue
        vendor, product = match.group("vendor"), match.group("product")
        if any(v.search(vendor) and p.search(product) for v, p in patterns):
            continue
        description = name if wwid == name else "%s (%s)" % (name, wwid)
        blocked.append("%s %s,%s" % (description, vendor, product))
    return blocked


class FilterModule(object):
    def filters(self):
        return {"multipath_unlisted_maps": multipath_unlisted_maps}
