# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

"""Exercise the actual Secret template through Ansible's renderer."""

from pathlib import Path

import pytest
import yaml
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar

ROOT = Path(__file__).resolve().parents[4]


@pytest.mark.parametrize("enabled", [None, False, True, "false", "true"])
def test_lower_priority_advertisement_option(enabled):
    defaults = yaml.safe_load((ROOT / "roles/keepalived/defaults/main.yml").read_text())
    tasks = yaml.safe_load((ROOT / "roles/keepalived/tasks/main.yml").read_text())
    secret = next(
        obj
        for obj in tasks[0]["kubernetes.core.k8s"]["definition"]
        if obj["kind"] == "Secret"
    )
    variables = {
        **defaults,
        "keepalived_interface": "eth0",
        "keepalived_vip": "192.0.2.10",
        "keepalived_vrid": 42,
        "keepalived_password": "fixture",
    }
    if enabled is not None:
        variables["keepalived_lower_prio_no_advert"] = enabled
    config = Templar(loader=DataLoader(), variables=variables).template(
        secret["stringData"]["keepalived.conf"]
    )
    wanted = enabled in (True, "true")
    assert ("lower_prio_no_advert true" in config) is wanted
    assert config.count("lower_prio_no_advert") == int(wanted)
    assert "{%" not in config and "{{" not in config
    assert config.count("{") == config.count("}") == 4
    assert "virtual_router_id 42" in config
    assert "priority 150\n  nopreempt" in config
    assert "auth_pass fixture" in config
