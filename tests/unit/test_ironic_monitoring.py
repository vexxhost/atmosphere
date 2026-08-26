# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path

import yaml
from ansible.parsing.dataloader import DataLoader
from ansible.template import Templar

REPOSITORY_ROOT = Path(__file__).parents[2]


def _load_tasks(role):
    return yaml.safe_load(
        (REPOSITORY_ROOT / "roles" / role / "tasks" / "main.yml").read_text()
    )


def _task_named(tasks, name):
    return next(task for task in tasks if task.get("name") == name)


def test_ironic_prometheus_exporter_uses_generic_extra_containers():
    tasks = _load_tasks("ironic")
    task = _task_named(tasks, "Add Ironic Prometheus exporter Helm values")
    values = task["ansible.builtin.set_fact"]["_ironic_effective_helm_values"]

    assert "'extraContainers': _ironic_conductor_extra_containers + [" in values
    assert ".get('ironic_conductor')" in values
    assert "'command': ['uwsgi']" in values
    assert "'ironic_prometheus_exporter':" not in values


def test_ironic_prometheus_exporter_preserves_mount_lists():
    tasks = _load_tasks("ironic")
    task = _task_named(tasks, "Add Ironic Prometheus exporter Helm values")
    values = task["ansible.builtin.set_fact"]["_ironic_effective_helm_values"]

    assert "'volumeMounts': _ironic_conductor_volume_mounts + [" in values
    assert "'volumes': _ironic_conductor_volumes + [" in values
    assert "'emptyDir': {}" in values


def test_ironic_prometheus_exporter_composes_with_existing_lists():
    tasks = _load_tasks("ironic")
    task = _task_named(tasks, "Add Ironic Prometheus exporter Helm values")
    expression = task["ansible.builtin.set_fact"]["_ironic_effective_helm_values"]
    existing_container = {"name": "existing-sidecar", "image": "example/sidecar"}
    existing_mount = {"name": "existing-volume", "mountPath": "/existing"}
    existing_volume = {"name": "existing-volume", "emptyDir": {}}
    effective_values = {
        "images": {"tags": {"ironic_conductor": "example/ironic@sha256:test"}},
        "conductor": {"extraContainers": [existing_container]},
        "pod": {
            "mounts": {
                "ironic_conductor": {
                    "ironic_conductor": {
                        "volumeMounts": [existing_mount],
                        "volumes": [existing_volume],
                    }
                }
            }
        },
    }
    variables = {
        "_ironic_effective_helm_values": effective_values,
        "_ironic_notification_drivers": ["messagingv2"],
        "_ironic_conductor_extra_containers": [existing_container],
        "_ironic_conductor_volume_mounts": [existing_mount],
        "_ironic_conductor_volumes": [existing_volume],
        "ironic_prometheus_exporter_port": 19608,
        "ironic_prometheus_exporter_workers": 2,
        "ironic_prometheus_exporter_collect_undeployed_nodes": False,
        "ironic_prometheus_exporter_sensor_interval": 600,
        "ironic_prometheus_exporter_image_pull_policy": "IfNotPresent",
        "ironic_prometheus_exporter_resources": {},
    }

    rendered = Templar(loader=DataLoader(), variables=variables).template(expression)
    containers = rendered["conductor"]["extraContainers"]
    mounts = rendered["pod"]["mounts"]["ironic_conductor"]["ironic_conductor"]

    assert containers[0] == existing_container
    assert containers[1]["name"] == "ironic-prometheus-exporter"
    assert containers[1]["image"] == "example/ironic@sha256:test"
    assert containers[1]["args"][1] == "0.0.0.0:19608"
    assert mounts["volumeMounts"][0] == existing_mount
    assert mounts["volumes"][0] == existing_volume
    assert rendered["conf"]["ironic"]["oslo_messaging_notifications"]["driver"][
        "values"
    ] == ["messagingv2", "prometheus_exporter"]


def test_ironic_prometheus_exporter_rejects_reserved_name_collisions():
    tasks = _load_tasks("ironic")
    task = _task_named(tasks, "Validate existing Ironic exporter Helm values")
    conditions = "\n".join(task["ansible.builtin.assert"]["that"])

    assert "'ironic-prometheus-exporter' not in" in conditions
    assert "'ironic-prometheus-metrics' not in" in conditions
    assert "'/var/lib/ironic/metrics' not in" in conditions


def test_ironic_prometheus_exporter_rejects_scalar_multistring_values():
    tasks = _load_tasks("ironic")
    task = _task_named(tasks, "Validate existing Ironic notification driver format")
    condition = task["ansible.builtin.assert"]["that"][0]

    sequence_branch, mapping_branch = condition.split("or (")[1:]

    assert "is not string" in sequence_branch
    assert "is not mapping" in sequence_branch
    assert "is not string" in mapping_branch
    assert "is not mapping" in mapping_branch


def test_ironic_podmonitor_uses_ironic_release_namespace():
    tasks = _load_tasks("kube_prometheus_stack")
    task = _task_named(tasks, "Manage Ironic Prometheus exporter PodMonitor")
    definition = task["kubernetes.core.k8s"]["definition"]

    assert definition["spec"]["namespaceSelector"]["matchNames"] == [
        "{{ ironic_helm_release_namespace | default('openstack') }}"
    ]


def test_dashboard_manifests_are_rendered_before_kubernetes_parsing():
    tasks = _load_tasks("kube_prometheus_stack")
    task = _task_named(tasks, "Deploy additional dashboards")
    module_args = task["kubernetes.core.k8s"]

    assert "template" not in module_args
    assert module_args["definition"] == (
        "{{ lookup('ansible.builtin.template', "
        "'configmap-dashboard.yaml.j2') | from_yaml }}"
    )
