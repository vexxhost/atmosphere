# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

import json
import subprocess
from inspect import signature
from pathlib import Path

import pytest
import yaml
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


def trident_templar(overrides=None):
    loader = DataLoader()
    defaults = load_vars(loader, ROOT / "roles/trident_csi/defaults/main.yml")
    variables = load_vars(loader, ROOT / "roles/trident_csi/vars/main.yml")
    images = load_vars(loader, ROOT / "roles/defaults/vars/main.yml")[
        "_atmosphere_images"
    ]
    return Templar(
        loader=loader,
        variables={
            **defaults,
            **variables,
            "role_path": str(ROOT / "roles/trident_csi"),
            "atmosphere_image_prefix": "mirror.example/",
            "atmosphere_images": {
                k: v for k, v in images.items() if k.startswith("trident")
            },
            "trident_csi_management_lif": "192.0.2.10",
            "trident_csi_username": "test",
            "trident_csi_password": "test",
            **(overrides or {}),
        },
    )


def test_trident_backend_and_storage_class_options():
    templar = trident_templar()
    assert (
        templar.template(trust_as_template("{{ trident_csi_configure_san }}")) is True
    )
    options = templar.template(trust_as_template("{{ _trident_csi_backend_options }}"))
    assert "useREST" not in options
    assert options["defaults"]["nameTemplate"].startswith("{{ .config.StoragePrefix }}")
    parameters = templar.template(
        trust_as_template("{{ _trident_csi_storage_class_parameters }}")
    )
    assert parameters == {"backendType": "ontap-san", "fsType": "ext4"}


@pytest.mark.parametrize(
    "protocol, driver, fs_type, rest",
    [
        ("iscsi", "ontap-san", "ext4", None),
        ("fc", "ontap-san", "ext4", None),
        ("nvme", "ontap-san", "ext4", True),
        ("nfs", "ontap-nas", "nfs", None),
        ("smb", "ontap-nas", None, None),
    ],
)
def test_trident_protocol_defaults(protocol, driver, fs_type, rest):
    templar = trident_templar(
        {"trident_csi_access_protocol": protocol, "trident_csi_storage_driver": driver}
    )
    options = templar.template(trust_as_template("{{ _trident_csi_backend_options }}"))
    assert options.get("useREST") is rest
    parameters = templar.template(
        trust_as_template("{{ _trident_csi_storage_class_parameters }}")
    )
    assert parameters.get("fsType") == fs_type
    backend = yaml.safe_load(
        templar.template(
            trust_as_template(
                (ROOT / "roles/trident_csi/templates/backend.yaml.j2").read_text()
            )
        )
    )
    assert backend["spec"]["storagePrefix"] == "atmosphere_"
    assert backend["spec"]["defaults"]["nameTemplate"].startswith(
        "{{ .config.StoragePrefix }}"
    )


@pytest.mark.parametrize(
    "override",
    [
        {"trident_csi_use_rest": False},
        {"trident_csi_backend_options": {"useREST": False}},
    ],
)
def test_nvme_rejects_zapi(override):
    templar = trident_templar({"trident_csi_access_protocol": "nvme", **override})
    tasks = load_vars(DataLoader(), ROOT / "roles/trident_csi/tasks/main.yml")
    validation = next(
        t["ansible.builtin.assert"]
        for t in tasks
        if t["name"] == "Validate NVMe backend API"
    )
    assert (
        templar.template(trust_as_template("{{ " + validation["that"][0] + " }}"))
        is False
    )


def test_operator_images_and_telemetry(tmp_path):
    templar = trident_templar({"trident_csi_namespace": "custom-trident"})
    options = templar.template(
        trust_as_template("{{ _trident_csi_orchestrator_options }}")
    )
    assert options["silenceAutosupport"] is True
    assert options["tridentImage"].startswith(
        "mirror.example/docker.io/netapp/trident:"
    )
    assert "@sha256:" in options["tridentImage"]
    values = templar.template(trust_as_template("{{ _trident_csi_helm_values }}"))
    values_file = tmp_path / "values.yaml"
    values_file.write_text(yaml.safe_dump(json.loads(json.dumps(values))))
    result = subprocess.run(
        [
            "helm",
            "template",
            "trident",
            str(ROOT / "charts/trident-operator"),
            "--namespace",
            "custom-trident",
            "-f",
            str(values_file),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    objects = [o for o in yaml.safe_load_all(result.stdout) if o]
    assert not any(o["kind"] == "TridentOrchestrator" for o in objects)
    deployment = next(o for o in objects if o["kind"] == "Deployment")
    assert deployment["metadata"]["namespace"] == "custom-trident"
    operator = deployment["spec"]["template"]["spec"]["containers"][0]
    assert operator["image"] == values["operatorImage"]
    env = {e["name"]: e["value"] for e in operator["env"] if "value" in e}
    for name, image in values["operatorExtraEnv"].items():
        assert env[name] == image
        assert image.startswith("mirror.example/")
        assert "@sha256:" in image
    images = []

    def collect_images(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "image":
                    images.append(item)
                else:
                    collect_images(item)
        elif isinstance(value, list):
            for item in value:
                collect_images(item)

    collect_images(objects)
    assert images
    assert all(
        image.startswith("mirror.example/") and "@sha256:" in image for image in images
    )
