# Copyright (c) 2023 VEXXHOST, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

import pytest
import yaml
from ansible_collections.vexxhost.atmosphere.plugins.filter.openstack_helm_image_tags import (
    openstack_helm_image_tags,
)


@pytest.fixture
def defaults():
    path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "..",
        "roles",
        "defaults",
        "vars",
        "main.yml",
    )

    with open(path) as fd:
        return yaml.safe_load(fd)


@pytest.fixture
def atmosphere_images(defaults):
    return defaults["_atmosphere_images"]


def test_openstack_helm_image_tags_for_magnum(atmosphere_images):
    assert openstack_helm_image_tags(atmosphere_images, "magnum") == {
        "bootstrap": "registry.atmosphere.dev/library/heat:{{ atmosphere_release }}",
        "db_drop": "registry.atmosphere.dev/library/heat:{{ atmosphere_release }}",
        "db_init": "registry.atmosphere.dev/library/heat:{{ atmosphere_release }}",
        "dep_check": "registry.atmosphere.dev/library/kubernetes-entrypoint:{{ atmosphere_release }}",
        "ks_endpoints": "registry.atmosphere.dev/library/heat:{{ atmosphere_release }}",
        "ks_service": "registry.atmosphere.dev/library/heat:{{ atmosphere_release }}",
        "ks_user": "registry.atmosphere.dev/library/heat:{{ atmosphere_release }}",
        "magnum_api": "registry.atmosphere.dev/library/magnum:{{ atmosphere_release }}",
        "magnum_conductor": "registry.atmosphere.dev/library/magnum:{{ atmosphere_release }}",
        "magnum_db_sync": "registry.atmosphere.dev/library/magnum:{{ atmosphere_release }}",
        "rabbit_init": "docker.io/library/rabbitmq:3.13.3-management",
    }
