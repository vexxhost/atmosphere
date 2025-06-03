# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-26T17:38:39Z

FROM golang AS octavia-test-server
# renovate: name=openstack/octavia-tempest-plugin repo=https://opendev.org/openstack/octavia-tempest-plugin.git branch=master
ARG OCTAVIA_TEMPEST_PLUGIN_GIT_REF=fd803099c2c602fc5e8df1d4bcf25b1e585e4b51
ADD --keep-git-dir=true https://opendev.org/openstack/octavia-tempest-plugin.git#${OCTAVIA_TEMPEST_PLUGIN_GIT_REF} /src
RUN GO111MODULE=off CGO_ENABLED=0 GOOS=linux go build \
    -a -ldflags '-s -w -extldflags -static' \
    -o /build/test_server.bin \
    /src/octavia_tempest_plugin/contrib/test_server/test_server.go

FROM openstack-venv-builder AS build
ADD --keep-git-dir=true https://opendev.org/openstack/requirements.git#2023.2-eol /src/requirements
RUN git -C /src/requirements fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/tempest.git#2023.2-eol /src/tempest
RUN git -C /src/tempest fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/barbican-tempest-plugin.git#2023.2-eol /src/barbican-tempest-plugin
RUN git -C /src/barbican-tempest-plugin fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/cinder-tempest-plugin.git#2023.2-eol /src/cinder-tempest-plugin
RUN git -C /src/cinder-tempest-plugin fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/heat-tempest-plugin.git#2023.2-eol /src/heat-tempest-plugin
RUN git -C /src/heat-tempest-plugin fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/keystone-tempest-plugin.git#2023.2-eol /src/keystone-tempest-plugin
RUN git -C /src/keystone-tempest-plugin fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/neutron-tempest-plugin.git#2023.2-eol /src/neutron-tempest-plugin
RUN git -C /src/neutron-tempest-plugin fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/octavia-tempest-plugin.git#2023.2-eol /src/octavia-tempest-plugin
RUN git -C /src/octavia-tempest-plugin fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
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
