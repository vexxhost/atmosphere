# Copyright (c) 2026 VEXXHOST, Inc.
# SPDX-License-Identifier: Apache-2.0

import os
import re

import pytest
import yaml
from ansible.errors import AnsibleFilterError
from ansible_collections.vexxhost.atmosphere.plugins.filter.resolve_images import (
    FilterModule,
    resolve_images,
)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
FIXTURE = os.path.join(ROOT, "internal", "releasemanifest", "testdata", "resolve.yaml")
VARS = os.path.join(ROOT, "roles", "defaults", "vars", "main.yml")

with open(FIXTURE) as f:
    CASES = yaml.safe_load(f)["cases"]


@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_shared_cases(case):
    """Run the cases shared with the Go implementation."""
    kwargs = {
        "prefix": case.get("prefix", ""),
        "mirrors": case.get("mirrors") or [],
        "strip_prefix": case.get("strip_prefix", False),
    }
    if case.get("error"):
        with pytest.raises(AnsibleFilterError):
            resolve_images({"image": case["input"]}, **kwargs)
        return
    assert resolve_images({"image": case["input"]}, **kwargs) == {
        "image": case["expected"]
    }


def _source_images(prefix):
    with open(VARS) as f:
        images = yaml.safe_load(f)["_atmosphere_images"]
    values = {
        "atmosphere_image_prefix": prefix,
        "atmosphere_kubernetes_version": "1.28.13",
        "ceph_version": "18.2.7",
    }
    return {
        key: re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: values[m.group(1)], value)
        for key, value in images.items()
    }


@pytest.mark.parametrize(
    "prefix", ["", "harbor.example.com/", "harbor.example.com/proxy-"]
)
def test_source_images_are_unchanged_without_rules(prefix):
    """Existing prefix users get exactly the references they got before."""
    images = _source_images(prefix)
    assert resolve_images(images, prefix=prefix, strip_prefix=True) == images


def test_source_images_resolve_with_rules():
    images = _source_images("harbor.example.com/")
    resolved = resolve_images(
        images,
        prefix="harbor.example.com/",
        mirrors=[
            {"source": "docker.io", "mirror": "harbor.example.com/dockerhub-proxy"}
        ],
        strip_prefix=True,
    )
    assert (
        resolved["haproxy"] == "harbor.example.com/dockerhub-proxy/library/haproxy:2.5"
    )
    assert resolved["ceph"] == images["ceph"]
    registries = {value.split("/", 1)[0] for value in resolved.values()}
    assert registries == {"harbor.example.com"}


@pytest.mark.parametrize(
    "rule",
    [
        {"source": "quay.io"},
        {"source": "quay.io", "mirror": ""},
        {"source": "quay.io/ceph/ceph:v1", "mirror": "mirror.example.com/ceph"},
        {"source": "quay.io", "mirror": "mirror.example.com", "extra": True},
    ],
)
def test_invalid_rules(rule):
    with pytest.raises(AnsibleFilterError):
        resolve_images({"ceph": "quay.io/ceph/ceph:v18.2.7"}, mirrors=[rule])


def test_filter_is_registered():
    assert FilterModule().filters()["resolve_images"] is resolve_images
