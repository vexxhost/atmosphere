# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
SPEC = importlib.util.spec_from_file_location(
    "discovery", ROOT / "roles/kubernetes_upgrade_compatibility/files/discovery.py"
)
discovery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(discovery)


def test_does_not_resume_a_reused_process_id(tmp_path, monkeypatch):
    signals = []
    monkeypatch.setattr(discovery, "process_identity", lambda pid: None)
    monkeypatch.setattr(discovery.os, "kill", lambda *args: signals.append(args))
    state = {
        "active": True,
        "kind": "percona",
        "processes": [{"pid": 123, "started": "old"}],
    }
    assert discovery.restore(tmp_path / "state.json", state)
    assert signals == []


def test_nfd_restoration_refuses_concurrent_config_changes(tmp_path, monkeypatch):
    state = {
        "active": True,
        "kind": "nfd",
        "namespace": "monitoring",
        "name": "worker-conf",
        "uid": "expected",
        "original": "original",
        "suppressed": "suppressed",
    }
    monkeypatch.setattr(
        discovery,
        "kubectl",
        lambda *a: json.dumps(
            {
                "metadata": {"uid": "expected"},
                "data": {"nfd-worker.conf": "changed-by-someone-else"},
            }
        ),
    )
    with pytest.raises(RuntimeError, match="refusing"):
        discovery.restore(tmp_path / "state.json", state)
    assert state["active"]


@pytest.mark.parametrize(
    "text", ["NoPublish:false", '"NoPublish":false', '\\"NoPublish\\":false']
)
def test_nfd_reload_checks_stable_identity_and_actual_configuration(text, monkeypatch):
    pod = {
        "metadata": {"name": "worker-a", "uid": "uid"},
        "status": {
            "containerStatuses": [
                {"name": "worker", "containerID": "containerd://id", "restartCount": 0}
            ]
        },
    }
    state = {
        "namespace": "monitoring",
        "workers": json.loads(json.dumps({"worker-a": discovery.worker_identity(pod)})),
    }
    monkeypatch.setattr(discovery, "workers", lambda state: [pod])
    monkeypatch.setattr(
        discovery, "kubectl", lambda *a: "configuration successfully updated " + text
    )
    discovery.wait_nfd_loaded(state, "2026-01-01T00:00:00Z", False)
