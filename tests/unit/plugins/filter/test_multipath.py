# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

import pytest
from ansible.errors import AnsibleFilterError
from ansible_collections.vexxhost.atmosphere.plugins.filter.multipath import (
    FilterModule,
    multipath_unlisted_maps,
)

OUTPUT = """\
mpatha (3600a098038303634722b4d59646c4436) dm-0 NETAPP,LUN C-Mode
size=10G features='3 queue_if_no_path pg_init_retries 50' hwhandler='1 alua' wp=rw
|-+- policy='service-time 0' prio=50 status=active
| `- 1:0:0:0 sdb 8:16 active ready running
`-+- policy='service-time 0' prio=10 status=enabled
  `- 2:0:0:0 sdc 8:32 active ready running
3624a93701c0d5b4d3a5c4e2b00011001 dm-1 PURE,FlashArray
size=20G features='0' hwhandler='1 alua' wp=rw
`-+- policy='service-time 0' prio=50 status=active
  `- 3:0:0:1 sdd 8:48 active ready running
eui.00a1b2c3d4e5f60724a937 dm-2 NVME,Pure Storage FlashArray
size=5G features='0' hwhandler='0' wp=rw
`-+- policy='queue-length 0' prio=50 status=active
  `- 0:0:1:1 nvme0n1 259:1 active ready running
"""

NETAPP = [
    {"vendor": "NETAPP", "product": "LUN.*"},
    {"vendor": "NVME", "product": "^NetApp ONTAP Controller.*"},
]
PURE = [
    {"vendor": "PURE", "product": "FlashArray"},
    {"vendor": "NVME", "product": "Pure Storage FlashArray"},
]


def test_all_maps_allowed():
    assert multipath_unlisted_maps(OUTPUT, NETAPP + PURE) == []


def test_omitted_array_maps_reported():
    assert multipath_unlisted_maps(OUTPUT, NETAPP) == [
        "3624a93701c0d5b4d3a5c4e2b00011001 PURE,FlashArray",
        "eui.00a1b2c3d4e5f60724a937 NVME,Pure Storage FlashArray",
    ]


def test_alias_reported_with_wwid():
    assert multipath_unlisted_maps(OUTPUT, PURE) == [
        "mpatha (3600a098038303634722b4d59646c4436) NETAPP,LUN C-Mode"
    ]


def test_excluded_wwids_ignored():
    assert (
        multipath_unlisted_maps(
            OUTPUT,
            PURE,
            ["3600a098038303634722b4d59646c4436"],
        )
        == []
    )


@pytest.mark.parametrize("output", ["", None, "No multipath kernel module loaded\n"])
def test_no_maps(output):
    assert multipath_unlisted_maps(output, NETAPP) == []


def test_invalid_device_entry():
    with pytest.raises(AnsibleFilterError):
        multipath_unlisted_maps(OUTPUT, [{"vendor": "("}])


def test_filter_registered():
    assert FilterModule().filters()["multipath_unlisted_maps"] is (
        multipath_unlisted_maps
    )
