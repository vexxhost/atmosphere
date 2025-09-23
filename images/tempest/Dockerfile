# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM golang AS octavia-test-server
# renovate: name=openstack/octavia-tempest-plugin repo=https://github.com/openstack/octavia-tempest-plugin.git branch=master
ARG OCTAVIA_TEMPEST_PLUGIN_GIT_REF=2f3e8a379573dc8c7cb13a5395f55ba00790fe59
ADD --keep-git-dir=true https://github.com/openstack/octavia-tempest-plugin.git#${OCTAVIA_TEMPEST_PLUGIN_GIT_REF} /src
RUN GO111MODULE=off CGO_ENABLED=0 GOOS=linux go build \
    -a -ldflags '-s -w -extldflags -static' \
    -o /build/test_server.bin \
    /src/octavia_tempest_plugin/contrib/test_server/test_server.go

FROM openstack-venv-builder AS build
# renovate: name=openstack/requirements repo=https://github.com/openstack/requirements.git branch=master
ARG REQUIREMENTS_GIT_REF=46a7e3927152884c05f1e257c528af593d67b84d
ADD --keep-git-dir=true https://github.com/openstack/requirements.git#${REQUIREMENTS_GIT_REF} /src/requirements
RUN git -C /src/requirements fetch --unshallow
# renovate: name=openstack/tempest repo=https://github.com/openstack/tempest.git branch=master
ARG TEMPEST_GIT_REF=538f6af8da510e9286ddc762182cfa7170ad7b03
ADD --keep-git-dir=true https://github.com/openstack/tempest.git#${TEMPEST_GIT_REF} /src/tempest
RUN git -C /src/tempest fetch --unshallow
# renovate: name=openstack/barbican-tempest-plugin repo=https://github.com/openstack/barbican-tempest-plugin.git branch=master
ARG BARBICAN_TEMPEST_PLUGIN_GIT_REF=2cd185133a86242c58d721e66c2db753a369fe60
ADD --keep-git-dir=true https://github.com/openstack/barbican-tempest-plugin.git#${BARBICAN_TEMPEST_PLUGIN_GIT_REF} /src/barbican-tempest-plugin
RUN git -C /src/barbican-tempest-plugin fetch --unshallow
# renovate: name=openstack/cinder-tempest-plugin repo=https://github.com/openstack/cinder-tempest-plugin.git branch=master
ARG CINDER_TEMPEST_PLUGIN_GIT_REF=1357d5dccffc2cd6c1e8a13e84c065d5bd55e4d5
ADD --keep-git-dir=true https://github.com/openstack/cinder-tempest-plugin.git#${CINDER_TEMPEST_PLUGIN_GIT_REF} /src/cinder-tempest-plugin
RUN git -C /src/cinder-tempest-plugin fetch --unshallow
# renovate: name=openstack/heat-tempest-plugin repo=https://github.com/openstack/heat-tempest-plugin.git branch=master
ARG HEAT_TEMPEST_PLUGIN_GIT_REF=1ce78d2eba96678955e3be10096fc239b08ba809
ADD --keep-git-dir=true https://github.com/openstack/heat-tempest-plugin.git#${HEAT_TEMPEST_PLUGIN_GIT_REF} /src/heat-tempest-plugin
RUN git -C /src/heat-tempest-plugin fetch --unshallow
# renovate: name=openstack/keystone-tempest-plugin repo=https://github.com/openstack/keystone-tempest-plugin.git branch=master
ARG KEYSTONE_TEMPEST_PLUGIN_GIT_REF=bab7165ee8aef4abb796db587299c773bc105ee1
ADD --keep-git-dir=true https://github.com/openstack/keystone-tempest-plugin.git#${KEYSTONE_TEMPEST_PLUGIN_GIT_REF} /src/keystone-tempest-plugin
RUN git -C /src/keystone-tempest-plugin fetch --unshallow
# renovate: name=openstack/neutron-tempest-plugin repo=https://github.com/openstack/neutron-tempest-plugin.git branch=master
ARG NEUTRON_TEMPEST_PLUGIN_GIT_REF=9c22c14682afa1168d0e1bd1cd1efb092c28a8fe
ADD --keep-git-dir=true https://github.com/openstack/neutron-tempest-plugin.git#${NEUTRON_TEMPEST_PLUGIN_GIT_REF} /src/neutron-tempest-plugin
RUN git -C /src/neutron-tempest-plugin fetch --unshallow
# renovate: name=openstack/octavia-tempest-plugin repo=https://github.com/openstack/octavia-tempest-plugin.git branch=master
ARG OCTAVIA_TEMPEST_PLUGIN_GIT_REF=2f3e8a379573dc8c7cb13a5395f55ba00790fe59
ADD --keep-git-dir=true https://github.com/openstack/octavia-tempest-plugin.git#${OCTAVIA_TEMPEST_PLUGIN_GIT_REF} /src/octavia-tempest-plugin
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
