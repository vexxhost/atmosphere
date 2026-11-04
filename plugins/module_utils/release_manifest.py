# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

"""Shared logic for Atmosphere release manifests.

The resolution rules here must match ``internal/releasemanifest`` in Go; both
implementations run the shared cases in
``internal/releasemanifest/testdata/resolve.yaml``.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import hashlib
import json
import os
import re
import ssl
from urllib.error import HTTPError
from urllib.parse import urlencode, urljoin
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

import yaml

API_VERSION = "atmosphere.vexxhost.com/v1alpha1"
KIND = "ReleaseManifest"
ARTIFACT_TYPE = "application/vnd.vexxhost.atmosphere.release.v1"
MEDIA_TYPE = "application/vnd.vexxhost.atmosphere.release.v1+yaml"

_PATH_COMPONENT = re.compile(r"^[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*$")
_TAG = re.compile(r"^[a-zA-Z0-9_][a-zA-Z0-9._-]{0,127}$")
_DIGEST = re.compile(r"^sha256:[a-f0-9]{64}$")
_CHALLENGE = re.compile(r'(\w+)="([^"]*)"')

_MANIFEST_ACCEPT = ", ".join(
    [
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.oci.artifact.manifest.v1+json",
    ]
)


class ReleaseManifestError(Exception):
    pass


class Reference(object):
    """A fully qualified image reference: host/path[:tag][@digest]."""

    def __init__(self, repository, tag="", digest=""):
        self.repository = repository
        self.tag = tag
        self.digest = digest

    @classmethod
    def parse(cls, value):
        if not isinstance(value, str):
            raise ReleaseManifestError("image reference %r is not a string" % (value,))

        rest, digest = value, ""
        if "@" in rest:
            rest, digest = rest.split("@", 1)
            if not _DIGEST.match(digest):
                raise ReleaseManifestError("invalid digest in %r" % value)

        tag = ""
        last_slash = rest.rfind("/")
        last_colon = rest.rfind(":")
        if last_colon > last_slash:
            tag_start = last_colon + 1
            rest, tag = rest[:last_colon], rest[tag_start:]
            if not _TAG.match(tag):
                raise ReleaseManifestError("invalid tag in %r" % value)

        if last_slash < 0:
            raise ReleaseManifestError(
                "image %r is not fully qualified (missing registry)" % value
            )

        host, path = rest.split("/", 1)
        if host != "localhost" and "." not in host and ":" not in host:
            raise ReleaseManifestError(
                "image %r is not fully qualified (missing registry)" % value
            )
        for component in path.split("/"):
            if not _PATH_COMPONENT.match(component):
                raise ReleaseManifestError(
                    "invalid repository path component %r in %r" % (component, value)
                )

        if not tag and not digest:
            raise ReleaseManifestError(
                "image %r has neither a tag nor a digest" % value
            )

        return cls(rest, tag, digest)

    @property
    def registry(self):
        return self.repository.split("/", 1)[0]

    @property
    def path(self):
        return self.repository.split("/", 1)[1]

    def __str__(self):
        value = self.repository
        if self.tag:
            value += ":" + self.tag
        if self.digest:
            value += "@" + self.digest
        return value


def _validate_rule(rule):
    if not isinstance(rule, dict) or set(rule) != {"source", "mirror"}:
        raise ReleaseManifestError(
            "mirror rules must have exactly a 'source' and a 'mirror': %r" % (rule,)
        )
    for name in ("source", "mirror"):
        value = rule[name]
        if not isinstance(value, str) or not value:
            raise ReleaseManifestError("mirror rule %s must not be empty" % name)
        if value.endswith("/") or "@" in value or " " in value:
            raise ReleaseManifestError(
                "mirror rule %s %r must be a registry, namespace or repository without a tag or digest"
                % (name, value)
            )
        last = value.rsplit("/", 1)[-1]
        if ":" in last and "/" in value:
            raise ReleaseManifestError(
                "mirror rule %s %r must not contain a tag" % (name, value)
            )


def resolve_image(value, prefix="", mirrors=None, strip_prefix=False):
    """Return the image reference to deploy for a canonical image.

    The most specific mirror rule matching the image repository replaces the
    matching part of the repository. Images that no rule matches get the
    image prefix.

    With ``strip_prefix``, the input already carries the prefix (the source
    image list in the defaults role): the prefix is removed before matching
    rules, and values that no rule matches are returned unchanged.
    """
    prefix = prefix or ""
    if strip_prefix and not mirrors:
        return value

    canonical = value
    if strip_prefix and prefix and canonical.startswith(prefix):
        canonical = canonical[len(prefix) :]  # noqa: E203

    ref = Reference.parse(canonical)

    best = None
    for rule in mirrors or []:
        _validate_rule(rule)
        source = rule["source"]
        if ref.repository == source or ref.repository.startswith(source + "/"):
            if best is None or len(source) > len(best["source"]):
                best = rule

    if best is None:
        return value if strip_prefix else prefix + canonical

    suffix = ref.repository[len(best["source"]) :]  # noqa: E203
    ref.repository = best["mirror"] + suffix
    return str(ref)


def resolve_images(images, prefix="", mirrors=None, strip_prefix=False):
    if not isinstance(images, dict):
        raise ReleaseManifestError(
            "images must be a mapping, got %s" % type(images).__name__
        )
    resolved = {}
    for key, value in images.items():
        try:
            resolved[key] = resolve_image(value, prefix, mirrors, strip_prefix)
        except ReleaseManifestError as e:
            raise ReleaseManifestError("image %r: %s" % (key, e))
    return resolved


def validate_manifest(manifest):
    if not isinstance(manifest, dict):
        raise ReleaseManifestError("release manifest must be a mapping")
    if manifest.get("apiVersion") != API_VERSION:
        raise ReleaseManifestError(
            "unsupported apiVersion %r (expected %r)"
            % (manifest.get("apiVersion"), API_VERSION)
        )
    if manifest.get("kind") != KIND:
        raise ReleaseManifestError(
            "unsupported kind %r (expected %r)" % (manifest.get("kind"), KIND)
        )
    images = manifest.get("images")
    if not isinstance(images, dict) or not images:
        raise ReleaseManifestError("release manifest contains no images")
    for key, value in images.items():
        if not Reference.parse(value).digest:
            raise ReleaseManifestError(
                "image %r (%s) is not pinned by digest" % (key, value)
            )
    return manifest


def images_for_kubernetes_version(manifest, kubernetes_version):
    """Return the manifest images for the Kubernetes version being deployed.

    The control plane images are pinned for the default Kubernetes version.
    When another version is deployed, they fall back to the tag for that
    version, which is how they are referenced without a manifest.
    """
    images = dict(manifest["images"])
    kubernetes = manifest.get("kubernetes") or {}
    pinned_version = str(kubernetes.get("version") or "")
    if not kubernetes_version or str(kubernetes_version) == pinned_version:
        return images

    for key in kubernetes.get("images") or []:
        ref = Reference.parse(images[key])
        images[key] = "%s:v%s" % (ref.repository, kubernetes_version)
    return images


def _docker_auth(host, docker_config=None):
    path = docker_config or os.path.join(
        os.environ.get("DOCKER_CONFIG", os.path.expanduser("~/.docker")), "config.json"
    )
    try:
        with open(path) as f:
            auths = json.load(f).get("auths", {})
    except (IOError, OSError, ValueError):
        return None
    for name in (
        host,
        "https://" + host,
        "index.docker.io" if host == "registry-1.docker.io" else None,
    ):
        if name and auths.get(name, {}).get("auth"):
            return auths[name]["auth"]
    return None


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class _RegistryClient(object):
    def __init__(
        self, host, plain_http=False, timeout=30, docker_config=None, ca_file=None
    ):
        self.api_host = "registry-1.docker.io" if host == "docker.io" else host
        self.base = "%s://%s" % ("http" if plain_http else "https", self.api_host)
        self.timeout = timeout
        self.basic = _docker_auth(self.api_host, docker_config)
        self.authorization = None
        context = ssl.create_default_context()
        if ca_file:
            # Trust this CA in addition to the system certificates.
            context.load_verify_locations(cafile=ca_file)
        self.opener = build_opener(HTTPSHandler(context=context), _NoRedirect)

    def _open(self, url, headers):
        try:
            return self.opener.open(Request(url, headers=headers), timeout=self.timeout)
        except HTTPError as e:
            return e

    def _token(self, challenge):
        params = dict(_CHALLENGE.findall(challenge))
        realm = params.pop("realm", None)
        if not realm:
            raise ReleaseManifestError(
                "registry %s returned an invalid authentication challenge"
                % self.api_host
            )
        headers = {"Authorization": "Basic " + self.basic} if self.basic else {}
        response = self._open(realm + "?" + urlencode(params), headers)
        if response.getcode() != 200:
            raise ReleaseManifestError(
                "authentication with %s failed (HTTP %s)"
                % (self.api_host, response.getcode())
            )
        body = json.loads(response.read().decode("utf-8"))
        token = body.get("token") or body.get("access_token")
        if not token:
            raise ReleaseManifestError(
                "registry %s did not return a token" % self.api_host
            )
        return "Bearer " + token

    def get(self, path, accept=None):
        url = self.base + path
        for _ in range(5):
            headers = {"Accept": accept} if accept else {}
            if self.authorization:
                headers["Authorization"] = self.authorization
            response = self._open(url, headers)
            code = response.getcode()

            if code == 401 and not self.authorization:
                challenge = response.headers.get("WWW-Authenticate", "")
                if challenge.lower().startswith("bearer"):
                    self.authorization = self._token(challenge)
                elif self.basic:
                    self.authorization = "Basic " + self.basic
                else:
                    raise ReleaseManifestError(
                        "registry %s requires credentials" % self.api_host
                    )
                continue

            if code in (301, 302, 303, 307, 308):
                location = urljoin(url, response.headers["Location"])
                # Blob redirects point at storage that must not receive the
                # registry credentials.
                redirected = self._open(location, {"Accept": accept} if accept else {})
                if redirected.getcode() != 200:
                    raise ReleaseManifestError(
                        "fetching %s failed (HTTP %s)"
                        % (location, redirected.getcode())
                    )
                return redirected.read()

            if code != 200:
                raise ReleaseManifestError("fetching %s failed (HTTP %s)" % (url, code))
            return response.read()

        raise ReleaseManifestError("too many authentication attempts for %s" % url)


def _split_location(location):
    if "@" in location:
        repository, reference = location.split("@", 1)
        return repository, reference
    last_slash = location.rfind("/")
    last_colon = location.rfind(":")
    if last_colon > last_slash:
        tag_start = last_colon + 1
        return location[:last_colon], location[tag_start:]
    raise ReleaseManifestError(
        "%s is neither a file nor an OCI reference with a tag or digest" % location
    )


def _verify(data, digest):
    algorithm, expected = digest.split(":", 1)
    if algorithm != "sha256" or hashlib.sha256(data).hexdigest() != expected:
        raise ReleaseManifestError("content does not match digest %s" % digest)


def fetch_manifest(
    location, plain_http=False, timeout=30, docker_config=None, ca_file=None
):
    """Download a release manifest published as an OCI artifact."""
    repository, reference = _split_location(location)
    if "/" not in repository:
        raise ReleaseManifestError(
            "%s is not a fully qualified OCI reference" % location
        )
    host, path = repository.split("/", 1)
    client = _RegistryClient(
        host,
        plain_http=plain_http,
        timeout=timeout,
        docker_config=docker_config,
        ca_file=ca_file,
    )

    raw = client.get("/v2/%s/manifests/%s" % (path, reference), accept=_MANIFEST_ACCEPT)
    if reference.startswith("sha256:"):
        _verify(raw, reference)

    artifact = json.loads(raw.decode("utf-8"))
    if artifact.get("artifactType") != ARTIFACT_TYPE:
        raise ReleaseManifestError(
            "%s is not an Atmosphere release manifest (artifact type %r)"
            % (location, artifact.get("artifactType"))
        )

    for layer in artifact.get("layers") or []:
        if layer.get("mediaType") != MEDIA_TYPE:
            continue
        data = client.get("/v2/%s/blobs/%s" % (path, layer["digest"]))
        _verify(data, layer["digest"])
        return validate_manifest(yaml.safe_load(data))

    raise ReleaseManifestError(
        "%s does not contain a %s layer" % (location, MEDIA_TYPE)
    )


def resolve_location(location, prefix="", mirrors=None):
    """Return where to read a release manifest from.

    File paths are used as they are. OCI references are resolved with the
    image prefix and mirror rules, like every image, so that deployments
    using a registry cache or mirror also read the manifest through it.
    """
    if os.path.isfile(location):
        return location
    return resolve_image(location, prefix=prefix, mirrors=mirrors)


def load_manifest(
    location, plain_http=False, timeout=30, docker_config=None, ca_file=None
):
    """Load a release manifest from a file or an OCI reference."""
    if os.path.isfile(location):
        with open(location) as f:
            return validate_manifest(yaml.safe_load(f))
    return fetch_manifest(
        location,
        plain_http=plain_http,
        timeout=timeout,
        docker_config=docker_config,
        ca_file=ca_file,
    )
