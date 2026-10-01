# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

RESOURCES = (
    "instances",
    "cores",
    "ram",
    "volumes",
    "gigabytes",
    "secgroups",
    "secgroup-rules",
)
ROOT = Path(__file__).resolve().parents[3]

CLI = r"""
import json
import os
from pathlib import Path
import sys

state_path = Path(os.environ["QUOTA_TEST_STATE"])
state = json.loads(state_path.read_text())
args = sys.argv[1:]
assert args[:3] == ["--os-cloud", "atmosphere", "quota"]
assert args[-1] == state["project"]
state["calls"].append(args[3])
if args[3] == "show":
    assert args[4:-1] == ["--all", "-f", "json"]
    state_path.write_text(json.dumps(state))
    if state.get("malformed"):
        print("not JSON")
    else:
        print(json.dumps([
            {"Resource": name, "Limit": value}
            for name, value in state["quotas"].items()
        ]))
elif args[3] == "set":
    expected = [part for name in state["quotas"] for part in ("--" + name, "-1")]
    assert args[4:-1] == expected
    if state.get("partial_failure") and state["calls"].count("set") == 1:
        state["quotas"]["instances"] = -1
        state_path.write_text(json.dumps(state))
        sys.exit(1)
    if not state.get("ignore_update"):
        state["quotas"] = dict.fromkeys(state["quotas"], -1)
    state_path.write_text(json.dumps(state))
else:
    raise AssertionError(args)
"""


@pytest.fixture(params=[("octavia", "admin"), ("manila", "service")])
def quota_playbook(request, tmp_path):
    role, project = request.param
    source = yaml.safe_load((ROOT / "roles" / role / "tasks/main.yml").read_text())
    block = copy.deepcopy(
        next(
            task
            for task in source
            if task["name"] == f"Ensure unlimited {project} project quotas"
        )
    )
    for task in block["block"]:
        if "retries" in task:
            task.update(retries=2, delay=0)
    playbook = tmp_path / "quota.yml"
    playbook.write_text(
        yaml.safe_dump(
            [{"hosts": "localhost", "gather_facts": False, "tasks": [block]}]
        )
    )
    executable = tmp_path / "openstack"
    executable.write_text(f"#!{sys.executable}\n" + CLI)
    executable.chmod(0o755)
    config = tmp_path / "ansible.cfg"
    config.write_text("[defaults]\n")
    state_file = tmp_path / "state.json"
    state_file.write_text(
        json.dumps(
            {"project": project, "quotas": dict.fromkeys(RESOURCES, 10), "calls": []}
        )
    )

    def run(check=False):
        command = [
            sys.executable,
            "-m",
            "ansible.cli.playbook",
            "-i",
            "localhost,",
            "-c",
            "local",
            "-e",
            f"ansible_python_interpreter={sys.executable}",
            str(playbook),
        ]
        if check:
            command.append("--check")
        return subprocess.run(
            command,
            cwd=tmp_path,
            env={
                **os.environ,
                "PATH": str(tmp_path) + os.pathsep + os.environ["PATH"],
                "QUOTA_TEST_STATE": str(state_file),
                "ANSIBLE_CONFIG": str(config),
                "ANSIBLE_NOCOLOR": "1",
                "ANSIBLE_STDOUT_CALLBACK": "default",
            },
            capture_output=True,
            text=True,
            timeout=60,
        )

    return state_file, run


def test_update_and_idempotent_rerun(quota_playbook):
    state_file, run = quota_playbook
    result = run()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "changed=1" in result.stdout
    state = json.loads(state_file.read_text())
    assert state["quotas"] == dict.fromkeys(RESOURCES, -1)
    assert state["calls"] == ["show", "set", "show"]
    result = run()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "changed=0" in result.stdout
    assert json.loads(state_file.read_text())["calls"] == [
        "show",
        "set",
        "show",
        "show",
    ]


@pytest.mark.parametrize("limit,changed", [(10, 1), (-1, 0)])
def test_check_mode_does_not_write(quota_playbook, limit, changed):
    state_file, run = quota_playbook
    state = json.loads(state_file.read_text())
    state["quotas"] = dict.fromkeys(RESOURCES, limit)
    state_file.write_text(json.dumps(state))
    result = run(check=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"changed={changed}" in result.stdout
    state["calls"] = ["show"]
    assert json.loads(state_file.read_text()) == state


@pytest.mark.parametrize("invalid", ["missing", "nonnumeric", "malformed"])
def test_invalid_output_fails_without_writing(quota_playbook, invalid):
    state_file, run = quota_playbook
    state = json.loads(state_file.read_text())
    if invalid == "missing":
        del state["quotas"]["volumes"]
    elif invalid == "nonnumeric":
        state["quotas"]["volumes"] = "unknown"
    else:
        state["malformed"] = True
    state_file.write_text(json.dumps(state))
    result = run()
    assert result.returncode != 0
    assert json.loads(state_file.read_text())["calls"] == ["show"]


def test_partial_update_is_retried(quota_playbook):
    state_file, run = quota_playbook
    state = json.loads(state_file.read_text())
    state["partial_failure"] = True
    state_file.write_text(json.dumps(state))
    result = run()
    assert result.returncode == 0, result.stdout + result.stderr
    state = json.loads(state_file.read_text())
    assert state["calls"] == ["show", "set", "set", "show"]
    assert state["quotas"] == dict.fromkeys(RESOURCES, -1)


def test_readback_detects_unsuccessful_update(quota_playbook):
    state_file, run = quota_playbook
    state = json.loads(state_file.read_text())
    state["ignore_update"] = True
    state_file.write_text(json.dumps(state))
    result = run()
    assert result.returncode != 0
    assert json.loads(state_file.read_text())["calls"] == [
        "show",
        "set",
        "show",
        "show",
        "show",
    ]
