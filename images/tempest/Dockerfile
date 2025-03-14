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
ARG TEMPEST_GIT_REF=50bd5aa470db2958018513ab43696dbb2596b30f
ADD --keep-git-dir=true https://opendev.org/openstack/tempest.git#${TEMPEST_GIT_REF} /src/tempest
RUN git -C /src/tempest fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/barbican-tempest-plugin.git#master /src/barbican-tempest-plugin
RUN git -C /src/barbican-tempest-plugin fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/cinder-tempest-plugin.git#master /src/cinder-tempest-plugin
RUN git -C /src/cinder-tempest-plugin fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/heat-tempest-plugin.git#master /src/heat-tempest-plugin
RUN git -C /src/heat-tempest-plugin fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/keystone-tempest-plugin.git#master /src/keystone-tempest-plugin
RUN git -C /src/keystone-tempest-plugin fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/neutron-tempest-plugin.git#master /src/neutron-tempest-plugin
RUN git -C /src/neutron-tempest-plugin fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/octavia-tempest-plugin.git#master /src/octavia-tempest-plugin
RUN git -C /src/octavia-tempest-plugin fetch --unshallow
ADD https://releases.openstack.org/constraints/upper/master /upper-constraints.txt
RUN --mount=type=cache,target=/root/.cache/uv <<EOF bash -xe
uv pip install \
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
