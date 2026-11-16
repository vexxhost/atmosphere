# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import yaml


def test_ironic_role_is_opt_in_and_follows_neutron():
    repository_root = Path(__file__).parents[2]
    plays = yaml.safe_load(
        (repository_root / "playbooks" / "openstack.yml").read_text()
    )

    openstack_play = next(
        play
        for play in plays
        if play.get("hosts") == "controllers[0]"
        and any(role.get("role") == "neutron" for role in play.get("roles", []))
    )
    roles = openstack_play["roles"]
    role_names = [role["role"] for role in roles]
    ironic = roles[role_names.index("ironic")]

    assert role_names.index("ironic") > role_names.index("neutron")
    assert ironic["when"] == ("atmosphere_ironic_enabled | default(false) | bool")
    assert ironic["tags"] == ["ironic"]


def test_disabled_ironic_role_cannot_expand_an_empty_endpoint_loop():
    repository_root = Path(__file__).parents[2]
    tasks = yaml.safe_load(
        (
            repository_root
            / "roles"
            / "openstack_helm_endpoints"
            / "tasks"
            / "main.yml"
        ).read_text()
    )
    task = next(
        task
        for task in tasks
        if task.get("name") == "Generate OpenStack-Helm endpoints"
    )

    assert task["loop"] == ("{{ openstack_helm_endpoints_list | default([], true) }}")
