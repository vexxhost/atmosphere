# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

import json
import re
import shlex
import subprocess
import sys
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
    variables = load_vars(loader, ROOT / "roles/multipathd/vars/main.yml")
    return Templar(
        loader=loader, variables={**defaults, **variables, **overrides}
    ).template(trust_as_template(value))


@pytest.mark.parametrize(
    "overrides, expected",
    [
        ({}, "yes"),
        ({"csi_driver": "trident"}, "yes"),
        ({"multipathd_arrays": ["netapp_ontap"]}, "no"),
        ({"multipathd_arrays": ["netapp_ontap", "pure_flasharray"]}, "no"),
        ({"multipathd_arrays": ["nimble"]}, "no"),
        ({"multipathd_find_multipaths": "strict"}, "strict"),
    ],
)
def test_multipath_policy(overrides, expected):
    assert render("{{ multipathd_find_multipaths }}", overrides) == expected


def multipath_config(overrides=None):
    text = render(
        (ROOT / "roles/multipathd/templates/multipath.conf.j2").read_text(),
        {"ansible_managed": "test", **(overrides or {})},
    )
    # Parse the rendered configuration, retaining repeated sections/keys.
    config = []
    stack = [config]
    for line in text.splitlines():
        tokens = shlex.split(line, comments=True)
        if not tokens:
            continue
        if tokens == ["}"]:
            stack.pop()
        elif tokens[-1] == "{":
            section = []
            stack[-1].append((tokens[0], section))
            stack.append(section)
        else:
            assert len(tokens) == 2, line
            stack[-1].append(tuple(tokens))
    assert len(stack) == 1
    return dict(config)


def test_legacy_config():
    config = multipath_config()
    assert dict(config["defaults"]) == {
        "user_friendly_names": "no",
        "find_multipaths": "yes",
    }
    devices = [dict(device) for _, device in config["devices"]]
    assert [device["vendor"] for device in devices] == ["NVME", "PURE", "Nimble"]
    assert [device["dev_loss_tmo"] for device in devices] == ["60", "600", "infinity"]
    assert [device["path_selector"] for device in devices] == [
        "queue-length 0",
        "service-time 0",
        "service-time 0",
    ]
    assert config["blacklist"] == [
        ("devnode", "^pxd[0-9]*"),
        ("devnode", "^pxd*"),
        ("device", [("vendor", "VMware"), ("product", "Virtual disk")]),
    ]
    assert "blacklist_exceptions" not in config


@pytest.mark.parametrize("csi_driver", ["trident", "rbd", "pure", None])
def test_shared_array_policy(csi_driver):
    # CSI and standalone OpenStack calls render the same host inventory.
    overrides = {"multipathd_arrays": ["netapp_ontap", "pure_flasharray"]}
    assert multipath_config(
        {**overrides, "csi_driver": csi_driver}
    ) == multipath_config(overrides)


@pytest.mark.parametrize(
    "vendor,product,allowed",
    [
        ("NETAPP", "LUN C-Mode", True),
        ("NVME", "NetApp ONTAP Controller", True),
        ("PURE", "FlashArray", True),
        ("ATA", "local-root", False),
        ("NVME", "Samsung local OSD", False),
        ("DellEMC", "PowerStore", False),
    ],
)
def test_array_device_filter(vendor, product, allowed):
    config = multipath_config(
        {"multipathd_arrays": ["netapp_ontap", "pure_flasharray"]}
    )
    assert dict(config["defaults"])["find_multipaths"] == "no"
    assert ("device", [("vendor", ".*"), ("product", ".*")]) in config["blacklist"]
    assert not any(key == "wwid" for key, _ in config["blacklist"])
    exceptions = [dict(device) for _, device in config["blacklist_exceptions"]]
    matches = any(
        re.search(d["vendor"], vendor) and re.search(d["product"], product)
        for d in exceptions
    )
    assert bool(matches) is allowed


def test_optional_wwid_exclusions():
    config = multipath_config(
        {
            "multipathd_arrays": ["netapp_ontap"],
            "multipathd_blacklist_wwids": ["excluded-lun"],
        }
    )
    assert ("wwid", "excluded-lun") in config["blacklist"]
    assert all(key == "device" for key, _ in config["blacklist_exceptions"])


@pytest.mark.parametrize("arrays,valid", [(["netapp_ontap"], True), (["typo"], False)])
def test_multipath_array_validation(arrays, valid):
    tasks = load_vars(DataLoader(), ROOT / "roles/multipathd/tasks/main.yml")
    validation = tasks[0]["ansible.builtin.assert"]["that"]
    results = [
        render("{{ " + condition + " }}", {"multipathd_arrays": arrays})
        for condition in validation
    ]
    assert all(results) is valid


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
            "ansible_system": "Linux",
            "ansible_os_family": "Debian",
            "ansible_kernel": "6.8.0-test",
            "ansible_distribution_major_version": "24",
            "multipathd_arrays": ["netapp_ontap"],
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


@pytest.mark.parametrize(
    "overrides,valid",
    [
        ({}, True),
        ({"multipathd_arrays": []}, False),
        ({"multipathd_arrays": ["pure_flasharray"]}, False),
        ({"multipathd_arrays": ["netapp_ontap", "pure_flasharray"]}, True),
        ({"multipathd_find_multipaths": "yes"}, False),
    ],
)
def test_trident_san_inventory_validation(overrides, valid):
    templar = trident_templar(overrides)
    tasks = load_vars(DataLoader(), ROOT / "roles/trident_csi/tasks/validate.yml")
    validation = next(
        t["ansible.builtin.assert"]["that"]
        for t in tasks
        if t["name"] == "Validate Trident SAN array selection"
    )
    assert (
        all(
            templar.template(trust_as_template("{{ " + condition + " }}"))
            for condition in validation
        )
        is valid
    )


@pytest.mark.parametrize(
    "protocol,driver,os_family,version,valid",
    [
        ("iscsi", "ontap-san", "Debian", "24", True),
        ("nfs", "ontap-nas", "RedHat", "8", True),
        ("smb", "ontap-nas", "Debian", "24", False),
        ("nvme", "ontap-san", "RedHat", "8", False),
        ("nvme", "ontap-san", "RedHat", "9", True),
    ],
)
def test_trident_node_protocol_validation(protocol, driver, os_family, version, valid):
    templar = trident_templar(
        {
            "trident_csi_access_protocol": protocol,
            "trident_csi_storage_driver": driver,
            "ansible_os_family": os_family,
            "ansible_distribution_major_version": version,
        }
    )
    tasks = load_vars(DataLoader(), ROOT / "roles/trident_csi/tasks/validate.yml")
    validation = tasks[0]["ansible.builtin.assert"]["that"]
    assert (
        all(
            templar.template(trust_as_template("{{ " + condition + " }}"))
            for condition in validation
        )
        is valid
    )


@pytest.mark.parametrize(
    "os_family,package", [("Debian", "nfs-common"), ("RedHat", "nfs-utils")]
)
def test_trident_nfs_client_tools(os_family, package):
    templar = trident_templar({"ansible_os_family": os_family})
    tasks = load_vars(DataLoader(), ROOT / "roles/trident_csi/tasks/hosts.yml")
    assert templar.template(tasks[0]["ansible.builtin.package"]["name"]) == package


@pytest.mark.parametrize(
    "os_family,package",
    [
        ("Debian", "linux-modules-extra-6.8.0-test"),
        ("RedHat", "kernel-modules-extra-6.8.0-test"),
    ],
)
def test_trident_nvme_kernel_tools(os_family, package):
    templar = trident_templar({"ansible_os_family": os_family})
    assert (
        templar.template(trust_as_template("{{ trident_csi_nvme_kernel_package }}"))
        == package
    )


@pytest.mark.parametrize(
    "fact,first,second,valid",
    [
        (
            "_trident_csi_iscsi_initiator",
            "iqn.2026-11.test:node1",
            "iqn.2026-11.test:node2",
            True,
        ),
        (
            "_trident_csi_iscsi_initiator",
            "iqn.2026-11.test:cloned",
            "iqn.2026-11.test:cloned",
            False,
        ),
        (
            "_trident_csi_nvme_hostnqn",
            "nqn.2026-11.test:node1",
            "nqn.2026-11.test:node2",
            True,
        ),
        (
            "_trident_csi_nvme_hostnqn",
            "nqn.2026-11.test:cloned",
            "nqn.2026-11.test:cloned",
            False,
        ),
    ],
)
def test_trident_identifier_uniqueness(tmp_path, fact, first, second, valid):
    # Exercise the actual run_once task with two local inventory hosts.
    tasks = yaml.safe_load((ROOT / "roles/trident_csi/tasks/hosts.yml").read_text())
    check = next(
        t for t in tasks if t["name"] == "Check unique Trident host identifiers"
    )
    inventory = tmp_path / "inventory.yml"
    inventory.write_text(
        yaml.safe_dump(
            {
                "all": {
                    "hosts": {
                        "node1": {"ansible_connection": "local", fact: first},
                        "node2": {"ansible_connection": "local", fact: second},
                    }
                }
            }
        )
    )
    playbook = tmp_path / "check.yml"
    playbook.write_text(
        yaml.safe_dump([{"hosts": "all", "gather_facts": False, "tasks": [check]}])
    )
    result = subprocess.run(
        [
            str(Path(sys.executable).with_name("ansible-playbook")),
            "-i",
            str(inventory),
            str(playbook),
        ],
        capture_output=True,
        text=True,
    )
    assert (result.returncode == 0) is valid, result.stdout + result.stderr
    if not valid:
        assert "Duplicate" in result.stdout, result.stdout + result.stderr


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
    tasks = load_vars(DataLoader(), ROOT / "roles/trident_csi/tasks/validate.yml")
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


def test_selected_array_devices():
    devices = render(
        "{{ _multipathd_selected_devices }}",
        {"multipathd_arrays": ["netapp_ontap", "pure_flasharray"]},
    )
    assert [(d["vendor"], d["product"]) for d in devices] == [
        ("NETAPP", "LUN.*"),
        ("NVME", "^NetApp ONTAP Controller.*"),
        ("PURE", "FlashArray"),
    ]


def test_active_map_check_precedes_configuration():
    tasks = load_vars(DataLoader(), ROOT / "roles/multipathd/tasks/main.yml")
    names = [t["name"] for t in tasks]
    assert names.index("Check active multipath maps are allowed") < names.index(
        "Install the configuration file"
    )
    check = tasks[names.index("Check active multipath maps are allowed")]
    assert "multipathd_check_active_maps | bool" in check["when"]
    assert "multipath_unlisted_maps" in check["vars"]["_multipathd_unlisted_maps"]


def test_csi_preparation_skips_other_drivers():
    play = load_vars(DataLoader(), ROOT / "playbooks/csi.yml")[0]
    assert play["hosts"] == "controllers"
    assert play["gather_facts"] is False
    (block,) = play["tasks"]
    assert block["when"] == "csi_driver | default('rbd') == 'trident'"
    assert "ansible.builtin.setup" in block["block"][0]


def test_trident_runs_on_control_plane():
    templar = trident_templar()
    selector = {"openstack-control-plane": "enabled"}
    orchestrator = templar.template(
        trust_as_template("{{ _trident_csi_orchestrator_options }}")
    )
    assert orchestrator["controllerPluginNodeSelector"] == selector
    assert orchestrator["nodePluginNodeSelector"] == selector
    helm_values = templar.template(trust_as_template("{{ _trident_csi_helm_values }}"))
    assert helm_values["nodeSelector"] == selector


@pytest.mark.parametrize("driver", ["ontap-san", "ontap-nas"])
def test_trident_backend_named_after_driver(driver):
    templar = trident_templar(
        {
            "trident_csi_storage_driver": driver,
            "trident_csi_access_protocol": "nfs" if driver == "ontap-nas" else "iscsi",
        }
    )
    backend = yaml.safe_load(
        templar.template(
            trust_as_template(
                (ROOT / "roles/trident_csi/templates/backend.yaml.j2").read_text()
            )
        )
    )
    assert backend["metadata"]["name"] == driver
    assert backend["spec"]["credentials"]["name"] == driver + "-secret"


def test_trident_name_template_truncates_request_name():
    templar = trident_templar()
    options = templar.template(trust_as_template("{{ _trident_csi_backend_options }}"))
    assert options["defaults"]["nameTemplate"].endswith(
        '{{ printf "%.63s" .volume.RequestName }}'
    )
