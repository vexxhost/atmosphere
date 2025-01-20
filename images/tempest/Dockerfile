# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM golang AS octavia-test-server
ADD --keep-git-dir=true https://opendev.org/openstack/octavia-tempest-plugin.git#master /src
RUN GO111MODULE=off CGO_ENABLED=0 GOOS=linux go build \
    -a -ldflags '-s -w -extldflags -static' \
    -o /build/test_server.bin \
    /src/octavia_tempest_plugin/contrib/test_server/test_server.go

FROM openstack-venv-builder AS build
ARG TEMPEST_GIT_REPO
ARG TEMPEST_GIT_REF
ADD --keep-git-dir=true ${TEMPEST_GIT_REPO}#${TEMPEST_GIT_REF} /src/tempest
RUN git -C /src/tempest fetch --unshallow
ARG BARBICAN_TEMPEST_PLUGIN_GIT_REPO
ARG BARBICAN_TEMPEST_PLUGIN_GIT_REF
ADD --keep-git-dir=true ${BARBICAN_TEMPEST_PLUGIN_GIT_REPO}#${BARBICAN_TEMPEST_PLUGIN_GIT_REF} /src/barbican-tempest-plugin
RUN git -C /src/barbican-tempest-plugin fetch --unshallow
ARG CINDER_TEMPEST_PLUGIN_GIT_REPO
ARG CINDER_TEMPEST_PLUGIN_GIT_REF
ADD --keep-git-dir=true ${CINDER_TEMPEST_PLUGIN_GIT_REPO}#${CINDER_TEMPEST_PLUGIN_GIT_REF} /src/cinder-tempest-plugin
RUN git -C /src/cinder-tempest-plugin fetch --unshallow
ARG HEAT_TEMPEST_PLUGIN_GIT_REPO
ARG HEAT_TEMPEST_PLUGIN_GIT_REF
ADD --keep-git-dir=true ${HEAT_TEMPEST_PLUGIN_GIT_REPO}#${HEAT_TEMPEST_PLUGIN_GIT_REF} /src/heat-tempest-plugin
RUN git -C /src/heat-tempest-plugin fetch --unshallow
ARG KEYSTONE_TEMPEST_PLUGIN_GIT_REPO
ARG KEYSTONE_TEMPEST_PLUGIN_GIT_REF
ADD --keep-git-dir=true ${KEYSTONE_TEMPEST_PLUGIN_GIT_REPO}#${KEYSTONE_TEMPEST_PLUGIN_GIT_REF} /src/keystone-tempest-plugin
RUN git -C /src/keystone-tempest-plugin fetch --unshallow
ARG NEUTRON_TEMPEST_PLUGIN_GIT_REPO
ARG NEUTRON_TEMPEST_PLUGIN_GIT_REF
ADD --keep-git-dir=true ${NEUTRON_TEMPEST_PLUGIN_GIT_REPO}#${NEUTRON_TEMPEST_PLUGIN_GIT_REF} /src/neutron-tempest-plugin
RUN git -C /src/neutron-tempest-plugin fetch --unshallow
ARG OCTAVIA_TEMPEST_PLUGIN_GIT_REPO
ARG OCTAVIA_TEMPEST_PLUGIN_GIT_REF
ADD --keep-git-dir=true ${OCTAVIA_TEMPEST_PLUGIN_GIT_REPO}#${OCTAVIA_TEMPEST_PLUGIN_GIT_REF} /src/octavia-tempest-plugin
RUN git -C /src/octavia-tempest-plugin fetch --unshallow
ADD https://releases.openstack.org/constraints/upper/master /upper-constraints.txt
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
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
