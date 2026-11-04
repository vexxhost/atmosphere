# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

import hashlib
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
import yaml
from ansible.errors import AnsibleLookupError
from ansible.plugins.loader import lookup_loader
from ansible_collections.vexxhost.atmosphere.plugins.lookup import release_manifest
from ansible_collections.vexxhost.atmosphere.plugins.module_utils.release_manifest import (
    ARTIFACT_TYPE,
    MEDIA_TYPE,
    ReleaseManifestError,
    fetch_manifest,
    images_for_kubernetes_version,
)

DIGEST_A = "sha256:1b9158ce28975f95def6a0ad459fa19f1336506074267a4b47c1bd914a00fec0"
DIGEST_B = "sha256:3095eaa3964b6b37b55d9de8681fb3d06cc247da1cd402fcdf81a7abbfc2496b"

MANIFEST = {
    "apiVersion": "atmosphere.vexxhost.com/v1alpha1",
    "kind": "ReleaseManifest",
    "release": "main",
    "kubernetes": {"version": "1.28.13", "images": ["kube_apiserver"]},
    "images": {
        "ceph": "quay.io/ceph/ceph:v18.2.7@" + DIGEST_A,
        "kube_apiserver": "registry.k8s.io/kube-apiserver:v1.28.13@" + DIGEST_B,
    },
}


def LookupModule():
    return lookup_loader.get("vexxhost.atmosphere.release_manifest")


@pytest.fixture(autouse=True)
def clear_cache():
    release_manifest._CACHE.clear()
    yield
    release_manifest._CACHE.clear()


@pytest.fixture
def manifest_file(tmp_path):
    path = tmp_path / "release-manifest.yaml"
    path.write_text(yaml.safe_dump(MANIFEST))
    return str(path)


def test_lookup_from_file(manifest_file):
    assert LookupModule().run([manifest_file], {}) == [MANIFEST["images"]]


def test_lookup_same_kubernetes_version_keeps_digest(manifest_file):
    result = LookupModule().run([manifest_file], {}, kubernetes_version="1.28.13")
    assert result == [MANIFEST["images"]]


def test_lookup_other_kubernetes_version_uses_tag(manifest_file):
    [images] = LookupModule().run([manifest_file], {}, kubernetes_version="1.29.4")
    assert images["kube_apiserver"] == "registry.k8s.io/kube-apiserver:v1.29.4"
    assert images["ceph"] == MANIFEST["images"]["ceph"]


def test_kubernetes_fallback_does_not_modify_manifest():
    images_for_kubernetes_version(MANIFEST, "1.29.4")
    assert MANIFEST["images"]["kube_apiserver"].endswith(DIGEST_B)


@pytest.mark.parametrize(
    "change",
    [
        {"apiVersion": "v0"},
        {"kind": "Other"},
        {"images": {}},
        {"images": {"ceph": "quay.io/ceph/ceph:v18.2.7"}},
    ],
)
def test_lookup_rejects_invalid_manifests(tmp_path, change):
    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump(dict(MANIFEST, **change)))
    with pytest.raises(AnsibleLookupError):
        LookupModule().run([str(path)], {})


def test_lookup_requires_location():
    with pytest.raises(AnsibleLookupError):
        LookupModule().run([""], {})


class FakeRegistry(object):
    """A minimal OCI registry with token authentication and blob redirects."""

    def __init__(self):
        self.layer = yaml.safe_dump(MANIFEST).encode()
        self.layer_digest = "sha256:" + hashlib.sha256(self.layer).hexdigest()
        self.artifact = json.dumps(
            {
                "schemaVersion": 2,
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "artifactType": ARTIFACT_TYPE,
                "config": {
                    "mediaType": "application/vnd.oci.empty.v1+json",
                    "digest": "sha256:44136fa355b3",
                    "size": 2,
                },
                "layers": [
                    {
                        "mediaType": MEDIA_TYPE,
                        "digest": self.layer_digest,
                        "size": len(self.layer),
                    }
                ],
            }
        ).encode()
        self.artifact_digest = "sha256:" + hashlib.sha256(self.artifact).hexdigest()
        self.requests = []

        registry = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _send(self, code, body=b"", headers=None):
                self.send_response(code)
                for key, value in (headers or {}).items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                auth = self.headers.get("Authorization")
                registry.requests.append((self.path, auth))
                port = self.server.server_address[1]

                if self.path.startswith("/token"):
                    return self._send(200, json.dumps({"token": "secret"}).encode())
                if self.path.startswith("/storage/"):
                    if auth:
                        return self._send(
                            400, b"credentials must not be sent to storage"
                        )
                    return self._send(200, registry.layer)
                if auth != "Bearer secret":
                    challenge = (
                        'Bearer realm="http://127.0.0.1:%d/token",service="fake",scope="repository:x:pull"'
                        % port
                    )
                    return self._send(401, headers={"WWW-Authenticate": challenge})
                if self.path in (
                    "/v2/vexxhost/atmosphere-release/manifests/v7.8.1",
                    "/v2/vexxhost/atmosphere-release/manifests/"
                    + registry.artifact_digest,
                ):
                    return self._send(200, registry.artifact)
                if self.path == "/v2/vexxhost/atmosphere-release/manifests/tampered":
                    return self._send(200, registry.artifact + b" ")
                if (
                    self.path
                    == "/v2/vexxhost/atmosphere-release/blobs/" + registry.layer_digest
                ):
                    return self._send(307, headers={"Location": "/storage/layer"})
                return self._send(404)

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.host = "127.0.0.1:%d" % self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def registry():
    registry = FakeRegistry()
    yield registry
    registry.close()


def test_fetch_manifest_from_registry(registry, tmp_path):
    location = registry.host + "/vexxhost/atmosphere-release:v7.8.1"
    assert (
        fetch_manifest(
            location, plain_http=True, docker_config=str(tmp_path / "none.json")
        )
        == MANIFEST
    )

    storage = [auth for path, auth in registry.requests if path.startswith("/storage/")]
    assert storage == [None]


def test_fetch_manifest_by_digest(registry, tmp_path):
    location = (
        registry.host + "/vexxhost/atmosphere-release@" + registry.artifact_digest
    )
    assert (
        fetch_manifest(
            location, plain_http=True, docker_config=str(tmp_path / "none.json")
        )
        == MANIFEST
    )

    tampered = registry.host + "/vexxhost/atmosphere-release@" + DIGEST_A
    with pytest.raises(ReleaseManifestError):
        fetch_manifest(
            tampered, plain_http=True, docker_config=str(tmp_path / "none.json")
        )


def test_lookup_from_registry_is_cached(registry):
    location = registry.host + "/vexxhost/atmosphere-release:v7.8.1"
    lookup = LookupModule()
    assert lookup.run([location], {}, plain_http=True) == [MANIFEST["images"]]
    count = len(registry.requests)
    assert lookup.run([location], {}, plain_http=True) == [MANIFEST["images"]]
    assert len(registry.requests) == count


def test_lookup_missing_reference(registry):
    with pytest.raises(AnsibleLookupError):
        LookupModule().run(
            [registry.host + "/vexxhost/atmosphere-release:missing"],
            {},
            plain_http=True,
        )


def _tls_files(tmp_path):
    """Create a private CA and a server certificate for 127.0.0.1."""
    import datetime
    import ipaddress

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID

    now = datetime.datetime.now(datetime.timezone.utc)
    validity = (now - datetime.timedelta(minutes=5), now + datetime.timedelta(hours=1))

    ca_key = ec.generate_private_key(ec.SECP256R1())
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test CA")])
    ca = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(validity[0])
        .not_valid_after(validity[1])
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(ca_key, hashes.SHA256())
    )

    key = ec.generate_private_key(ec.SECP256R1())
    cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "127.0.0.1")]))
        .issuer_name(ca_name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(validity[0])
        .not_valid_after(validity[1])
        .add_extension(
            x509.SubjectAlternativeName(
                [x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]
            ),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    ca_file = tmp_path / "ca.pem"
    ca_file.write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    cert_file = tmp_path / "cert.pem"
    cert_file.write_bytes(
        cert.public_bytes(serialization.Encoding.PEM)
        + key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    return str(ca_file), str(cert_file)


class TLSRegistry(object):
    """An HTTPS registry with basic authentication serving one manifest under
    any repository path."""

    def __init__(self, cert_file, username="ci", password="secret"):
        import base64
        import ssl

        self.layer = yaml.safe_dump(MANIFEST).encode()
        self.layer_digest = "sha256:" + hashlib.sha256(self.layer).hexdigest()
        self.artifact = json.dumps(
            {
                "schemaVersion": 2,
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "artifactType": ARTIFACT_TYPE,
                "layers": [{"mediaType": MEDIA_TYPE, "digest": self.layer_digest}],
            }
        ).encode()
        self.paths = []
        expected = (
            "Basic "
            + base64.b64encode(("%s:%s" % (username, password)).encode()).decode()
        )
        registry = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _send(self, code, body=b"", headers=None):
                self.send_response(code)
                for key, value in (headers or {}).items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                registry.paths.append(self.path)
                if self.headers.get("Authorization") != expected:
                    return self._send(
                        401, headers={"WWW-Authenticate": 'Basic realm="registry"'}
                    )
                if "/manifests/" in self.path:
                    return self._send(200, registry.artifact)
                if self.path.endswith("/blobs/" + registry.layer_digest):
                    return self._send(200, registry.layer)
                return self._send(404)

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(cert_file)
        self.server.socket = context.wrap_socket(self.server.socket, server_side=True)
        self.host = "127.0.0.1:%d" % self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def tls_registry(tmp_path, monkeypatch):
    import base64

    ca_file, cert_file = _tls_files(tmp_path)
    registry = TLSRegistry(cert_file)
    docker_dir = tmp_path / "docker"
    docker_dir.mkdir()
    (docker_dir / "config.json").write_text(
        json.dumps(
            {
                "auths": {
                    registry.host: {"auth": base64.b64encode(b"ci:secret").decode()}
                }
            }
        )
    )
    monkeypatch.setenv("DOCKER_CONFIG", str(docker_dir))
    registry.ca_file = ca_file
    yield registry
    registry.close()


def test_lookup_tls_registry_with_ca_file(tls_registry):
    location = tls_registry.host + "/vexxhost/atmosphere-release:ci"
    result = LookupModule().run([location], {}, ca_file=tls_registry.ca_file)
    assert result == [MANIFEST["images"]]


def test_lookup_tls_registry_rejects_unknown_ca(tls_registry):
    location = tls_registry.host + "/vexxhost/atmosphere-release:ci"
    with pytest.raises(AnsibleLookupError):
        LookupModule().run([location], {})


def test_lookup_tls_registry_requires_credentials(tls_registry, tmp_path, monkeypatch):
    monkeypatch.setenv("DOCKER_CONFIG", str(tmp_path / "missing"))
    location = tls_registry.host + "/vexxhost/atmosphere-release:ci"
    with pytest.raises(AnsibleLookupError):
        LookupModule().run([location], {}, ca_file=tls_registry.ca_file)


def test_lookup_applies_prefix_to_reference(tls_registry):
    LookupModule().run(
        ["ghcr.io/vexxhost/atmosphere-release:v7.9.0"],
        {},
        prefix=tls_registry.host + "/",
        ca_file=tls_registry.ca_file,
    )
    assert tls_registry.paths[-2:] == [
        "/v2/ghcr.io/vexxhost/atmosphere-release/manifests/v7.9.0",
        "/v2/ghcr.io/vexxhost/atmosphere-release/blobs/" + tls_registry.layer_digest,
    ]


def test_lookup_applies_mirror_rules_to_reference(tls_registry):
    LookupModule().run(
        ["ghcr.io/vexxhost/atmosphere-release:v7.9.0"],
        {},
        prefix="unused.example.com/",
        mirrors=[
            {"source": "ghcr.io/vexxhost", "mirror": tls_registry.host + "/mirror"}
        ],
        ca_file=tls_registry.ca_file,
    )
    assert tls_registry.paths[-1].startswith("/v2/mirror/atmosphere-release/blobs/")


def test_lookup_does_not_apply_prefix_to_files(manifest_file):
    result = LookupModule().run([manifest_file], {}, prefix="harbor.example.com/")
    assert result == [MANIFEST["images"]]
