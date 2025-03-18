# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-02-20T21:42:46Z

FROM golang AS octavia-test-server
ADD --keep-git-dir=true https://opendev.org/openstack/octavia-tempest-plugin.git#875c38f0355ecd31ce3a4ddf654d3adb8ea2370d /src
RUN GO111MODULE=off CGO_ENABLED=0 GOOS=linux go build \
    -a -ldflags '-s -w -extldflags -static' \
    -o /build/test_server.bin \
    /src/octavia_tempest_plugin/contrib/test_server/test_server.go

FROM openstack-venv-builder AS build
ADD --keep-git-dir=true https://opendev.org/openstack/requirements.git#7a304c74f76991597bfe7eb0666b2b2a2bf2ffa3 /src/requirements
RUN git -C /src/requirements fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/tempest.git#50bd5aa470db2958018513ab43696dbb2596b30f /src/tempest
RUN git -C /src/tempest fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/barbican-tempest-plugin.git#2cd185133a86242c58d721e66c2db753a369fe60 /src/barbican-tempest-plugin
RUN git -C /src/barbican-tempest-plugin fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/cinder-tempest-plugin.git#bb5594c061370316bfc881e24d11b3350fb0aef9 /src/cinder-tempest-plugin
RUN git -C /src/cinder-tempest-plugin fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/heat-tempest-plugin.git#d2db170988fe1ad3aedda997377b768a83ba9fe9 /src/heat-tempest-plugin
RUN git -C /src/heat-tempest-plugin fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/keystone-tempest-plugin.git#f3c89425613f333a1152a7d420e5d681154f7ad1 /src/keystone-tempest-plugin
RUN git -C /src/keystone-tempest-plugin fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/neutron-tempest-plugin.git#ed3744eba062bffa318f786c1370ecd2d0dae130 /src/neutron-tempest-plugin
RUN git -C /src/neutron-tempest-plugin fetch --unshallow
ADD --keep-git-dir=true https://opendev.org/openstack/octavia-tempest-plugin.git#875c38f0355ecd31ce3a4ddf654d3adb8ea2370d /src/octavia-tempest-plugin
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
