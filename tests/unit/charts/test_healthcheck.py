# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

import base64
import configparser
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
    "designate": ["api"],
    "glance": ["api"],
    "heat": ["api", "cfn"],
    "keystone": ["api"],
    "magnum": ["api"],
    "manila": ["api"],
    "neutron": ["server"],
    "nova": ["api-metadata", "api-osapi"],
    "octavia": ["api"],
}
CONFIG_FILES = {
    "barbican": "barbican-api-paste.ini",
    "glance": "glance-api-paste.ini",
    "keystone": "keystone.conf",
    "octavia": "octavia.conf",
}
ROOT_COMPOSITES = {
    "barbican": {"api": ["main"]},
    "cinder": {"api": ["osapi_volume"]},
    "designate": {"api": ["osapi_dns"]},
    "glance": {
        "api": [
            "glance-api",
            "glance-api-caching",
            "glance-api-cachemanagement",
            "glance-api-keystone",
            "glance-api-keystone+caching",
            "glance-api-keystone+cachemanagement",
        ]
    },
    "heat": {
        "api": ["heat-api", "heat-api-standalone", "heat-api-custombackend"],
        "cfn": ["heat-api-cfn", "heat-api-cfn-standalone"],
    },
    "magnum": {"api": ["main"]},
    "manila": {"api": ["osapi_share"]},
    "neutron": {"server": ["neutron"]},
    "nova": {"api-metadata": ["metadata"], "api-osapi": ["osapi_compute"]},
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
            manifests["configmap_etc"] = True
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
                    },
                    "oslo_messaging": {"port": {"amqp_tls": {"default": 5671}}},
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
            documents = [
                document for document in yaml.safe_load_all(result.stdout) if document
            ]
            deployments = [d for d in documents if d["kind"] == "Deployment"]
            secrets = {
                d["metadata"]["name"]: d for d in documents if d["kind"] == "Secret"
            }
            cache[chart, tls] = secrets, deployments
        return cache[chart, tls]

    return render


def mounted_config(chart, filename, container, volumes, secrets):
    path = f"/etc/{chart}/{filename}"
    mount = next(m for m in container["volumeMounts"] if m["mountPath"] == path)
    assert mount["subPath"] == filename
    secret = secrets[volumes[mount["name"]]["secret"]["secretName"]]
    config = configparser.ConfigParser(interpolation=None)
    config.read_string(base64.b64decode(secret["data"][filename]).decode())
    return config


@pytest.mark.parametrize(
    "chart,component",
    [
        (chart, component)
        for chart, components in DEPLOYMENTS.items()
        for component in components
    ],
    ids=[
        f"{chart}-{component}"
        for chart, components in DEPLOYMENTS.items()
        for component in components
    ],
)
def test_rendered_healthcheck_config_and_mounts(render_chart, chart, component):
    secrets, deployments = render_chart(chart)
    assert len(deployments) == len(DEPLOYMENTS[chart])
    deployment = next(
        d for d in deployments if d["metadata"]["name"] == f"{chart}-{component}"
    )
    pod = deployment["spec"]["template"]["spec"]
    volumes = {volume["name"]: volume for volume in pod["volumes"]}
    for container in pod["containers"]:
        if container["name"] == "nginx":
            continue
        config = mounted_config(
            chart, CONFIG_FILES.get(chart, "api-paste.ini"), container, volumes, secrets
        )
        if chart in ["keystone", "octavia"]:
            sections = [config["healthcheck"]]
            if chart == "octavia":
                assert config.getboolean("api_settings", "healthcheck_enabled")
        else:
            sections = []
            for root in ROOT_COMPOSITES[chart][component]:
                app = config[f"composite:{root}"]["/healthcheck"]
                section = config[f"app:{app}"]
                assert (
                    section["paste.app_factory"]
                    == "oslo_middleware:Healthcheck.app_factory"
                )
                sections.append(section)
        for section in sections:
            assert section["backends"] == "disable_by_file"
            assert section["disable_by_file_path"] == "/tmp/healthcheck_disable"
        if chart == "manila":
            service_config = mounted_config(
                chart, "manila.conf", container, volumes, secrets
            )
            assert (
                service_config["DEFAULT"]["api_paste_config"]
                == "/etc/manila/api-paste.ini"
            )
        marker = pathlib.PurePosixPath("/tmp/healthcheck_disable")
        mounts = [
            m
            for m in container["volumeMounts"]
            if marker.is_relative_to(m["mountPath"])
        ]
        mount = max(
            mounts, key=lambda m: len(pathlib.PurePosixPath(m["mountPath"]).parts)
        )
        assert not mount.get("readOnly", False)
        assert "emptyDir" in volumes[mount["name"]]
        assert container["readinessProbe"]["httpGet"]["path"] == "/healthcheck"
        for probe_name in ["readinessProbe", "livenessProbe"]:
            probe = container.get(probe_name)
            if probe:
                assert probe["httpGet"]["path"] == "/healthcheck"


def test_neutron_tls_nginx_healthcheck_probe(render_chart):
    _, deployments = render_chart("neutron", tls=True)
    nginx = next(
        c
        for d in deployments
        for c in d["spec"]["template"]["spec"]["containers"]
        if c["name"] == "nginx"
    )
    assert nginx["readinessProbe"]["httpGet"]["path"] == "/healthcheck"
    assert nginx["readinessProbe"]["httpGet"]["scheme"] == "HTTPS"


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
