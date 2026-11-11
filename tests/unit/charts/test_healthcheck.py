# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
import re
import shutil
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[3]
DEPLOYMENTS = {
    "barbican": ["api"],
    "cinder": ["api"],
    "glance": ["api"],
    "heat": ["api", "cfn"],
    "magnum": ["api"],
    "neutron": ["server"],
    "nova": ["api-metadata", "api-osapi"],
}
pytestmark = pytest.mark.skipif(shutil.which("helm") is None, reason="Helm is required")


@pytest.fixture(scope="module")
def render_chart():
    cache = {}

    def render(chart, tls=False):
        if (chart, tls) not in cache:
            chart_path = ROOT / "charts" / chart
            values = yaml.safe_load((chart_path / "values.yaml").read_text())
            manifests = {name: False for name in values["manifests"]}
            for deployment in DEPLOYMENTS[chart]:
                manifests["deployment_" + deployment.replace("-", "_")] = True
            manifests["certificates"] = tls
            overrides = {"manifests": manifests}
            if tls:
                service = "image" if chart == "glance" else "network"
                overrides["endpoints"] = {
                    service: {
                        "host_fqdn_override": {
                            "default": {
                                "tls": {
                                    "issuerRef": {"name": "test-issuer"},
                                    "secretName": chart + "-test-tls",
                                }
                            }
                        }
                    }
                }
            result = subprocess.run(
                [
                    "helm",
                    "template",
                    chart,
                    str(chart_path),
                    "-n",
                    "openstack",
                    "-f",
                    "-",
                ],
                input=json.dumps(overrides),
                text=True,
                capture_output=True,
                check=True,
            )
            deployments = [
                document
                for document in yaml.safe_load_all(result.stdout)
                if document and document.get("kind") == "Deployment"
            ]
            cache[chart, tls] = values, deployments
        return cache[chart, tls]

    return render


@pytest.mark.parametrize("chart", DEPLOYMENTS)
def test_disable_file_uses_writable_volume(render_chart, chart):
    values, deployments = render_chart(chart)
    marker = pathlib.PurePosixPath(
        values["conf"]["paste"]["app:healthcheck"]["disable_by_file_path"]
    )
    assert marker.is_absolute()
    assert len(deployments) == len(DEPLOYMENTS[chart])
    for deployment in deployments:
        pod = deployment["spec"]["template"]["spec"]
        volumes = {volume["name"]: volume for volume in pod["volumes"]}
        for container in pod["containers"]:
            if container["name"] == "nginx":
                continue
            mounts = [
                mount
                for mount in container["volumeMounts"]
                if marker.is_relative_to(mount["mountPath"])
                and not mount.get("readOnly", False)
                and "emptyDir" in volumes[mount["name"]]
            ]
            assert mounts, f"{deployment['metadata']['name']}: {marker} is not writable"
            for probe_name in ["readinessProbe", "livenessProbe"]:
                probe = container.get(probe_name)
                if probe:
                    assert probe["httpGet"]["path"] == "/healthcheck"


@pytest.mark.parametrize("chart", ["glance", "neutron"])
@pytest.mark.parametrize("probe_name", ["readinessProbe", "livenessProbe"])
@pytest.mark.parametrize("status", [200, 503, 500])
def test_tls_probe_http_status(render_chart, chart, probe_name, status):
    _, deployments = render_chart(chart, tls=True)
    container_name = "glance-api" if chart == "glance" else "neutron-server"
    container = next(
        container
        for deployment in deployments
        for container in deployment["spec"]["template"]["spec"]["containers"]
        if container["name"] == container_name
    )
    command = list(container[probe_name]["exec"]["command"])

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            assert self.path == "/healthcheck"
            self.send_response(status)
            self.end_headers()
            self.wfile.write(b"OK" if status == 200 else b"DISABLED BY FILE")

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        command[0] = sys.executable
        command[2] = re.sub(
            r"http://127\.0\.0\.1:\d+",
            f"http://127.0.0.1:{server.server_port}",
            command[2],
        )
        result = subprocess.run(command, capture_output=True, timeout=5)
        assert (result.returncode == 0) == (status == 200), result.stderr.decode()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
