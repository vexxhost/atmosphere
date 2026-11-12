#!/usr/bin/env python3
# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0
"""Temporary compatibility for pinned NFD and Percona during API disruption."""

import argparse
import fcntl
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

DIRECTORY = Path("/var/lib/atmosphere/kubernetes-upgrade")


def command(argv, timeout=20):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(argv[0] + " failed: " + result.stderr[-500:])
    return result.stdout


def kubectl(namespace, *args):
    return command(
        [
            "kubectl",
            "--kubeconfig=/etc/kubernetes/admin.conf",
            "--request-timeout=10s",
            "-n",
            namespace,
            *args,
        ]
    )


def save(path, state):
    temporary = path.with_suffix(".tmp")
    with temporary.open("w") as stream:
        json.dump(state, stream)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.chmod(0o600)
    temporary.replace(path)


def process_identity(pid):
    root = Path("/proc") / str(pid)
    try:
        return dict(
            pid=pid,
            started=root.joinpath("stat").read_text().rsplit(")", 1)[1].split()[19],
            executable=os.readlink(root / "exe"),
            command=hashlib.sha256(root.joinpath("cmdline").read_bytes()).hexdigest(),
        )
    except FileNotFoundError:
        return None


def percona_processes(namespace, prefix):
    containers = json.loads(command(["crictl", "ps", "-o", "json"]))["containers"]
    namespaces = set()
    for container in containers:
        labels = container.get("labels", {})
        if (
            container["metadata"]["name"] == "haproxy"
            and labels.get("io.kubernetes.pod.namespace") == namespace
            and labels.get("io.kubernetes.pod.name", "").startswith(prefix)
        ):
            pid = json.loads(command(["crictl", "inspect", container["id"]]))["info"][
                "pid"
            ]
            namespace_id = os.readlink("/proc/" + str(pid) + "/ns/pid")
            if namespace_id == os.readlink("/proc/1/ns/pid"):
                raise RuntimeError(
                    "refusing process-wide protection for a hostPID container"
                )
            namespaces.add(namespace_id)
    found = []
    for root in Path("/proc").iterdir():
        if not root.name.isdigit():
            continue
        try:
            if os.readlink(root / "ns/pid") not in namespaces:
                continue
            argv = root.joinpath("cmdline").read_bytes().split(b"\0")
            if not argv[0] or Path(os.fsdecode(argv[0])).name != "peer-list":
                continue
            state = root.joinpath("stat").read_text().rsplit(")", 1)[1].split()[0]
            if state in ("T", "t"):
                raise RuntimeError(
                    "peer discovery was already stopped by another owner"
                )
            identity = process_identity(int(root.name))
            if identity:
                found.append(identity)
        except (FileNotFoundError, ProcessLookupError):
            continue
    if namespaces and not found:
        raise RuntimeError(
            "Percona HAProxy containers exist but peer discovery was not found"
        )
    return found


def workers(state):
    return [
        pod
        for pod in json.loads(kubectl(state["namespace"], "get", "pods", "-o", "json"))[
            "items"
        ]
        if pod["metadata"]["name"].startswith(state["prefix"])
    ]


def worker_identity(pod):
    return dict(
        uid=pod["metadata"]["uid"],
        containers=[
            [c["name"], c.get("containerID"), c["restartCount"]]
            for c in pod["status"].get("containerStatuses", [])
        ],
    )


def patch_nfd(state, old, new):
    patch = [
        dict(op="test", path="/metadata/uid", value=state["uid"]),
        dict(op="test", path="/data/nfd-worker.conf", value=old),
        dict(op="replace", path="/data/nfd-worker.conf", value=new),
    ]
    kubectl(
        state["namespace"],
        "patch",
        "configmap",
        state["name"],
        "--type=json",
        "-p",
        json.dumps(patch),
    )


def wait_nfd_loaded(state, since, wanted):
    deadline = time.monotonic() + 240
    while True:
        pods = workers(state)
        if {p["metadata"]["name"]: worker_identity(p) for p in pods} != state[
            "workers"
        ]:
            raise RuntimeError("NFD worker identities changed during hot reload")
        loaded = True
        for pod in pods:
            log = kubectl(
                state["namespace"],
                "logs",
                pod["metadata"]["name"],
                "--since-time=" + since,
            )
            lines = [
                line
                for line in log.splitlines()
                if "configuration successfully updated" in line
            ]
            matches = re.findall(
                r'NoPublish(?:\\?"|\s)*[:=](?:\\?"|\s)*(true|false)',
                lines[-1] if lines else "",
                re.I,
            )
            loaded = (
                loaded and bool(matches) and (matches[-1].lower() == "true") == wanted
            )
        if loaded:
            return
        if time.monotonic() >= deadline:
            raise RuntimeError("NFD did not confirm its configuration hot reload")
        time.sleep(4)


def restore(path, state, wait=False):
    if not state.get("active"):
        return False
    if state["kind"] == "percona":
        for original in state["processes"]:
            if process_identity(original["pid"]) == original:
                os.kill(original["pid"], signal.SIGCONT)
    else:
        current = json.loads(
            kubectl(state["namespace"], "get", "configmap", state["name"], "-o", "json")
        )
        if current["metadata"]["uid"] != state["uid"]:
            raise RuntimeError("NFD ConfigMap was replaced; refusing stale restoration")
        value = current["data"]["nfd-worker.conf"]
        since = datetime.now(timezone.utc).isoformat()
        if value == state["suppressed"]:
            patch_nfd(state, value, state["original"])
            if wait:
                wait_nfd_loaded(
                    state,
                    since,
                    bool(
                        (yaml.safe_load(state["original"]) or {})
                        .get("core", {})
                        .get("noPublish", False)
                    ),
                )
        elif value != state["original"]:
            raise RuntimeError("NFD configuration changed; refusing to overwrite it")
    state["active"] = False
    save(path, state)
    return True


def launch_watchdog(path, state):
    with path.with_suffix(".log").open("ab") as log:
        subprocess.Popen(
            [
                sys.executable,
                __file__,
                "watchdog",
                "--kind",
                state["kind"],
                "--token",
                state["token"],
            ],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=log,
            start_new_session=True,
        )


def prepare(args, path):
    if path.exists():
        restore(path, json.loads(path.read_text()), wait=True)
    state = dict(
        kind=args.kind,
        token=uuid.uuid4().hex,
        active=True,
        expires=time.time() + args.timeout,
        namespace=args.namespace,
        name=args.name,
        prefix=args.prefix,
    )
    if args.kind == "nfd":
        text = kubectl(
            args.namespace,
            "get",
            "configmap",
            args.name,
            "--ignore-not-found",
            "-o",
            "json",
        )
        if not text.strip():
            return False
        cm = json.loads(text)
        original = cm["data"]["nfd-worker.conf"]
        config = yaml.safe_load(original) or {}
        if config.get("core", {}).get("noPublish", False):
            return False
        config.setdefault("core", {})["noPublish"] = True
        state.update(
            uid=cm["metadata"]["uid"],
            original=original,
            suppressed=json.dumps(config, separators=(",", ":")),
        )
        state["workers"] = {
            pod["metadata"]["name"]: worker_identity(pod) for pod in workers(state)
        }
        if not state["workers"]:
            raise RuntimeError("NFD configuration exists but no workers were found")
    else:
        state["processes"] = percona_processes(args.namespace, args.prefix)
        if not state["processes"]:
            return False
    save(path, state)
    launch_watchdog(path, state)
    try:
        if args.kind == "nfd":
            since = datetime.now(timezone.utc).isoformat()
            patch_nfd(state, state["original"], state["suppressed"])
            wait_nfd_loaded(state, since, True)
        else:
            for original in state["processes"]:
                if process_identity(original["pid"]) != original:
                    raise RuntimeError(
                        "peer discovery process changed before protection"
                    )
                os.kill(original["pid"], signal.SIGSTOP)
    except Exception:
        restore(path, state)
        raise
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["prepare", "restore", "watchdog"])
    parser.add_argument("--kind", choices=["nfd", "percona"], required=True)
    parser.add_argument("--namespace")
    parser.add_argument("--name")
    parser.add_argument("--prefix")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--token")
    args = parser.parse_args()
    os.umask(0o077)
    path = DIRECTORY / (args.kind + ".json")
    if args.action == "watchdog":
        while True:
            time.sleep(1)
            with path.with_suffix(".lock").open("a") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                state = json.loads(path.read_text())
                if state["token"] != args.token or not state["active"]:
                    return
                if time.time() >= state["expires"]:
                    try:
                        restore(path, state)
                        return
                    except (RuntimeError, subprocess.TimeoutExpired):
                        # The API may still be recovering. Retain ownership and
                        # retry instead of abandoning a suppressed ConfigMap.
                        pass
    with path.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.action == "prepare":
            changed = prepare(args, path)
        else:
            changed = (
                restore(path, json.loads(path.read_text()), wait=True)
                if path.exists()
                else False
            )
    print(json.dumps({"changed": changed, "kind": args.kind}))


if __name__ == "__main__":
    main()
