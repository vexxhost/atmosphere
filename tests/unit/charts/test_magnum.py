# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

import base64
import configparser
import json
import pathlib
import shutil
import subprocess

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[3]
pytestmark = pytest.mark.skipif(shutil.which("helm") is None, reason="Helm is required")


def render_magnum_config(overrides):
    chart = ROOT / "charts" / "magnum"
    values = yaml.safe_load((chart / "values.yaml").read_text())
    manifests = {name: False for name in values["manifests"]}
    manifests["configmap_etc"] = True
    result = subprocess.run(
        ["helm", "template", "magnum", str(chart), "-n", "openstack", "-f", "-"],
        input=json.dumps({"manifests": manifests, **overrides}),
        text=True,
        capture_output=True,
        check=True,
    )
    secret = next(
        d
        for d in yaml.safe_load_all(result.stdout)
        if d and d["kind"] == "Secret" and d["metadata"]["name"] == "magnum-etc"
    )
    config = configparser.ConfigParser(interpolation=None)
    config.read_string(base64.b64decode(secret["data"]["magnum.conf"]).decode())
    return config


@pytest.mark.parametrize(
    "overrides,expected",
    [
        ({}, "http://keystone-api.openstack.svc.cluster.local:5000/v3"),
        (
            {"endpoints": {"identity": {"path": {"default": "/"}}}},
            "http://keystone-api.openstack.svc.cluster.local:5000/v3",
        ),
        (
            {
                "endpoints": {
                    "identity": {
                        "scheme": {"internal": "https"},
                        "hosts": {"internal": "identity"},
                        "port": {"api": {"internal": 8443}},
                        "path": {"internal": "/identity/v3/"},
                    }
                }
            },
            "https://identity.openstack.svc.cluster.local:8443/identity/v3",
        ),
        (
            {
                "endpoints": {
                    "identity": {
                        "scheme": {"internal": "https"},
                        "host_fqdn_override": {
                            "internal": "identity.internal.example.com"
                        },
                        "port": {"api": {"internal": 443}},
                        "path": {"default": "/identity/"},
                    }
                }
            },
            "https://identity.internal.example.com/identity/v3",
        ),
        (
            {
                "conf": {
                    "magnum": {
                        "keystone_authtoken": {
                            "auth_uri": "https://legacy.example.com/identity/v2.0"
                        }
                    }
                }
            },
            "https://legacy.example.com/identity/v3",
        ),
        (
            {
                "conf": {
                    "magnum": {
                        "keystone_authtoken": {
                            "auth_uri": "https://legacy.example.com/identity/v3/"
                        }
                    }
                }
            },
            "https://legacy.example.com/identity/v3",
        ),
        (
            {
                "conf": {
                    "magnum": {
                        "keystone_authtoken": {
                            "www_authenticate_uri": "https://custom.example.com/v3/"
                        }
                    }
                }
            },
            "https://custom.example.com/v3/",
        ),
        (
            {
                "conf": {
                    "magnum": {"keystone_authtoken": {"www_authenticate_uri": None}}
                }
            },
            "http://keystone-api.openstack.svc.cluster.local:5000/v3",
        ),
    ],
    ids=[
        "chart-defaults",
        "atmosphere-unversioned-endpoint",
        "custom-internal-endpoint",
        "custom-host-and-proxy-path",
        "legacy-v2-auth-uri-override",
        "legacy-auth-uri-override",
        "explicit-www-authenticate-uri",
        "null-www-authenticate-uri",
    ],
)
def test_trustee_authentication_url(overrides, expected):
    config = render_magnum_config(overrides)
    assert config["keystone_authtoken"]["www_authenticate_uri"] == expected
