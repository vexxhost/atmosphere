# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

from inspect import signature
from pathlib import Path

import pytest
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar

try:
    from ansible.template import trust_as_template
except ImportError:
    # Ansible versions before 2.19 trust template strings by default.
    def trust_as_template(value):
        return value


ROOT = Path(__file__).resolve().parents[3]


def load_vars(loader, path):
    options = {}
    if "trusted_as_template" in signature(loader.load_from_file).parameters:
        options["trusted_as_template"] = True
    return loader.load_from_file(str(path), **options)


def render(value, overrides):
    loader = DataLoader()
    defaults = load_vars(loader, ROOT / "roles/multipathd/defaults/main.yml")
    if overrides.get("csi_driver") == "trident":
        defaults["_trident_csi_multipath_defaults"] = load_vars(
            loader, ROOT / "roles/trident_csi/vars/multipath.yml"
        )
    return Templar(loader=loader, variables={**defaults, **overrides}).template(
        trust_as_template(value)
    )


@pytest.mark.parametrize(
    "overrides, expected",
    [
        ({}, "yes"),
        ({"csi_driver": "rbd"}, "yes"),
        ({"csi_driver": "trident"}, "no"),
        (
            {
                "csi_driver": "trident",
                "trident_csi_storage_driver": "ontap-san-economy",
            },
            "no",
        ),
        ({"csi_driver": "trident", "trident_csi_storage_driver": "ontap-nas"}, "yes"),
        ({"csi_driver": "trident", "trident_csi_configure_san": False}, "yes"),
        ({"csi_driver": "trident", "trident_csi_configure_san": "false"}, "yes"),
        ({"csi_driver": "trident", "trident_csi_configure_multipath": False}, "yes"),
        ({"csi_driver": "trident", "trident_csi_configure_multipath": "false"}, "yes"),
        (
            {
                "csi_driver": "trident",
                "trident_csi_multipath_find_multipaths": "strict",
            },
            "strict",
        ),
        ({"csi_driver": "trident", "multipathd_find_multipaths": "strict"}, "strict"),
        ({"csi_driver": "trident", "trident_csi_san_storage_drivers": []}, "yes"),
    ],
)
def test_multipath_policy(overrides, expected):
    assert render("{{ multipathd_find_multipaths }}", overrides) == expected


def test_local_disk_exclusions():
    config = render(
        (ROOT / "roles/multipathd/templates/multipath.conf.j2").read_text(),
        {
            "ansible_managed": "test",
            "csi_driver": "trident",
            "multipathd_blacklist_wwids": ["local-root", "local-osd"],
        },
    )
    assert "find_multipaths no" in config
    assert 'wwid "local-root"' in config
    assert 'wwid "local-osd"' in config
    assert 'devnode "^pxd' in config
    assert 'vendor "VMware"' in config


def test_trident_applies_same_local_disk_exclusions():
    loader = DataLoader()
    tasks = load_vars(loader, ROOT / "roles/trident_csi/tasks/main.yml")
    task = next(
        t for t in tasks if t.get("register") == "_trident_csi_multipath_blacklist"
    )
    options = task["ansible.builtin.blockinfile"]
    overrides = {"multipathd_blacklist_wwids": ["local-root", "local-osd"]}
    assert render(options["state"], overrides) == "present"
    block = render(options["block"], overrides)
    assert 'wwid "local-root"' in block
    assert 'wwid "local-osd"' in block
    assert render(options["state"], {}) == "absent"


def test_trident_backend_and_storage_class_options():
    loader = DataLoader()
    defaults = load_vars(loader, ROOT / "roles/trident_csi/defaults/main.yml")
    variables = load_vars(loader, ROOT / "roles/trident_csi/vars/main.yml")
    templar = Templar(
        loader=loader,
        variables={
            **defaults,
            **variables,
            "role_path": str(ROOT / "roles/trident_csi"),
        },
    )
    assert (
        templar.template(trust_as_template("{{ trident_csi_configure_san }}")) is True
    )
    options = templar.template(trust_as_template("{{ _trident_csi_backend_options }}"))
    assert options["useREST"] is False
    assert "{{ .volume.Name }}" in options["defaults"]["nameTemplate"]
    parameters = templar.template(
        trust_as_template("{{ _trident_csi_storage_class_parameters }}")
    )
    assert parameters == {"backendType": "ontap-san", "fsType": "ext4"}
