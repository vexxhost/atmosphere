# SPDX-License-Identifier: Apache-2.0
# Copyright (c) VEXXHOST, Inc.

import copy

import pytest
from ansible.errors import AnsibleFilterError
from ansible_collections.vexxhost.atmosphere.plugins.filter.rules_merge import (
    rules_merge,
)

rules = {
    "ipmi-exporter": {
        "groups": [
            {
                "name": "rules",
                "rules": [
                    {
                        "alert": "IpmiCollectorDown",
                        "expr": "ipmi_up == 0",
                        "for": "16m",
                        "labels": {"severity": "P2"},
                    }
                ],
            },
            {
                "name": "rules",
                "rules": [
                    {
                        "alert": "IpmiCollectorDown",
                        "expr": "ipmi_up == 0",
                        "for": "15m",
                        "labels": {"severity": "P3"},
                    }
                ],
            },
        ]
    }
}

expectd_append_rules = {
    "ipmi-exporter": {
        "groups": [
            {
                "name": "rules",
                "rules": [
                    {
                        "alert": "IpmiCollectorDown",
                        "expr": "ipmi_up == 0",
                        "for": "16m",
                        "labels": {"severity": "P2"},
                    },
                    {
                        "alert": "IpmiCollectorDown",
                        "expr": "ipmi_up == 0",
                        "for": "15m",
                        "labels": {"severity": "P3"},
                    },
                ],
            }
        ]
    }
}

expectd_replace_rules = {
    "ipmi-exporter": {
        "groups": [
            {
                "name": "rules",
                "rules": [
                    {
                        "alert": "IpmiCollectorDown",
                        "expr": "ipmi_up == 0",
                        "for": "15m",
                        "labels": {"severity": "P3"},
                    }
                ],
            }
        ]
    }
}


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            [copy.deepcopy(rules), {"list_merge": "replace"}],
            expectd_replace_rules,
        ),
        (
            [copy.deepcopy(rules), {"list_merge": "append"}],
            expectd_append_rules,
        ),
        (
            [dict(), {"list_merge": "foo"}],
            "'replace' and 'append' are the only valid value for 'list_merge'",
        ),
        (
            [dict(), {"list_merge": "append", "bar": "foo"}],
            "'list_merge' is the only valid keyword argument",
        ),
    ],
)
def test_rules_merge(test_input, expected):
    if isinstance(expected, dict):
        with pytest.raises(AnsibleFilterError) as ex:
            rules_merge(test_input[0], **test_input[1])
        assert str(ex.value) == expected
    else:
        assert rules_merge(test_input[0], **test_input[1]) == expected
