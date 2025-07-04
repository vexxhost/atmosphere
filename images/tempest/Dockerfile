# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM golang AS octavia-test-server
# renovate: name=openstack/octavia-tempest-plugin repo=https://opendev.org/openstack/octavia-tempest-plugin.git branch=master
ARG OCTAVIA_TEMPEST_PLUGIN_GIT_REF=13cb2ec83d8457189030ab1be209c28186d85c69
ADD --keep-git-dir=true https://opendev.org/openstack/octavia-tempest-plugin.git#${OCTAVIA_TEMPEST_PLUGIN_GIT_REF} /src
RUN GO111MODULE=off CGO_ENABLED=0 GOOS=linux go build \
    -a -ldflags '-s -w -extldflags -static' \
    -o /build/test_server.bin \
    /src/octavia_tempest_plugin/contrib/test_server/test_server.go

FROM openstack-venv-builder AS build
# renovate: name=openstack/requirements repo=https://opendev.org/openstack/requirements.git branch=master
ARG REQUIREMENTS_GIT_REF=b4ff8192c6a725ad6cf4f46db487776196ef86a3
ADD --keep-git-dir=true https://opendev.org/openstack/requirements.git#${REQUIREMENTS_GIT_REF} /src/requirements
RUN git -C /src/requirements fetch --unshallow
# renovate: name=openstack/tempest repo=https://opendev.org/openstack/tempest.git branch=master
ARG TEMPEST_GIT_REF=de95a36f17404d3fa51bb49fc9cc44238f9e2fc7
ADD --keep-git-dir=true https://opendev.org/openstack/tempest.git#${TEMPEST_GIT_REF} /src/tempest
RUN git -C /src/tempest fetch --unshallow
# renovate: name=openstack/barbican-tempest-plugin repo=https://opendev.org/openstack/barbican-tempest-plugin.git branch=master
ARG BARBICAN_TEMPEST_PLUGIN_GIT_REF=2cd185133a86242c58d721e66c2db753a369fe60
ADD --keep-git-dir=true https://opendev.org/openstack/barbican-tempest-plugin.git#${BARBICAN_TEMPEST_PLUGIN_GIT_REF} /src/barbican-tempest-plugin
RUN git -C /src/barbican-tempest-plugin fetch --unshallow
# renovate: name=openstack/cinder-tempest-plugin repo=https://opendev.org/openstack/cinder-tempest-plugin.git branch=master
ARG CINDER_TEMPEST_PLUGIN_GIT_REF=5102371cefecc0bf90e8ff789b1159b3dc6a5229
ADD --keep-git-dir=true https://opendev.org/openstack/cinder-tempest-plugin.git#${CINDER_TEMPEST_PLUGIN_GIT_REF} /src/cinder-tempest-plugin
RUN git -C /src/cinder-tempest-plugin fetch --unshallow
# renovate: name=openstack/heat-tempest-plugin repo=https://opendev.org/openstack/heat-tempest-plugin.git branch=master
ARG HEAT_TEMPEST_PLUGIN_GIT_REF=63de1c25800d85eb2075de65c9b05f7ded87779d
ADD --keep-git-dir=true https://opendev.org/openstack/heat-tempest-plugin.git#${HEAT_TEMPEST_PLUGIN_GIT_REF} /src/heat-tempest-plugin
RUN git -C /src/heat-tempest-plugin fetch --unshallow
# renovate: name=openstack/keystone-tempest-plugin repo=https://opendev.org/openstack/keystone-tempest-plugin.git branch=master
ARG KEYSTONE_TEMPEST_PLUGIN_GIT_REF=2ca14a9df38ed3cc42a7e2a6b6d67400ebc5be62
ADD --keep-git-dir=true https://opendev.org/openstack/keystone-tempest-plugin.git#${KEYSTONE_TEMPEST_PLUGIN_GIT_REF} /src/keystone-tempest-plugin
RUN git -C /src/keystone-tempest-plugin fetch --unshallow
# renovate: name=openstack/neutron-tempest-plugin repo=https://opendev.org/openstack/neutron-tempest-plugin.git branch=master
ARG NEUTRON_TEMPEST_PLUGIN_GIT_REF=fcb52b56cba9d55996068c8ef807063514f92ca6
ADD --keep-git-dir=true https://opendev.org/openstack/neutron-tempest-plugin.git#${NEUTRON_TEMPEST_PLUGIN_GIT_REF} /src/neutron-tempest-plugin
RUN git -C /src/neutron-tempest-plugin fetch --unshallow
# renovate: name=openstack/octavia-tempest-plugin repo=https://opendev.org/openstack/octavia-tempest-plugin.git branch=master
ARG OCTAVIA_TEMPEST_PLUGIN_GIT_REF=13cb2ec83d8457189030ab1be209c28186d85c69
ADD --keep-git-dir=true https://opendev.org/openstack/octavia-tempest-plugin.git#${OCTAVIA_TEMPEST_PLUGIN_GIT_REF} /src/octavia-tempest-plugin
RUN git -C /src/octavia-tempest-plugin fetch --unshallow
RUN --mount=type=cache,target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /src/requirements/upper-constraints.txt \
        /src/tempest \
        /src/barbican-tempest-plugin \
        /src/cinder-tempest-plugin \
        /src/heat-tempest-plugin \
        /src/keystone-tempest-plugin \
        /src/neutron-tempest-plugin \
        /src/octavia-tempest-plugin
EOF

FROM openstack-python-runtime
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    iputils-ping openssh-client
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=octavia-test-server --link /build/test_server.bin /opt/octavia-tempest-plugin/test_server.bin
COPY --from=build --link /var/lib/openstack /var/lib/openstack
