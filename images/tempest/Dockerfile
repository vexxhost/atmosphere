# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-10-14T10:18:12Z

FROM golang AS octavia-test-server
# renovate: name=openstack/octavia-tempest-plugin repo=https://github.com/openstack/octavia-tempest-plugin.git branch=master
ARG OCTAVIA_TEMPEST_PLUGIN_GIT_REF=31ccc63c4f61c8f6a120cbe3f496da7c383c9a47
ADD --keep-git-dir=true https://github.com/openstack/octavia-tempest-plugin.git#${OCTAVIA_TEMPEST_PLUGIN_GIT_REF} /src
RUN GO111MODULE=off CGO_ENABLED=0 GOOS=linux go build \
    -a -ldflags '-s -w -extldflags -static' \
    -o /build/test_server.bin \
    /src/octavia_tempest_plugin/contrib/test_server/test_server.go

FROM openstack-venv-builder AS build
# renovate: name=openstack/requirements repo=https://github.com/openstack/requirements.git branch=master
ARG REQUIREMENTS_GIT_REF=73fb1fe9fc5f158ec49e33a79be73ba3641800f3
ADD --keep-git-dir=true https://github.com/openstack/requirements.git#${REQUIREMENTS_GIT_REF} /src/requirements
RUN git -C /src/requirements fetch --unshallow
# renovate: name=openstack/tempest repo=https://github.com/openstack/tempest.git branch=master
ARG TEMPEST_GIT_REF=93df2d2d3e73788db982be0f4b85e3451343c94c
ADD --keep-git-dir=true https://github.com/openstack/tempest.git#${TEMPEST_GIT_REF} /src/tempest
RUN git -C /src/tempest fetch --unshallow
# renovate: name=openstack/barbican-tempest-plugin repo=https://github.com/openstack/barbican-tempest-plugin.git branch=master
ARG BARBICAN_TEMPEST_PLUGIN_GIT_REF=debd1648449976dd92d9df165af19e11bd43424a
ADD --keep-git-dir=true https://github.com/openstack/barbican-tempest-plugin.git#${BARBICAN_TEMPEST_PLUGIN_GIT_REF} /src/barbican-tempest-plugin
RUN git -C /src/barbican-tempest-plugin fetch --unshallow
# renovate: name=openstack/cinder-tempest-plugin repo=https://github.com/openstack/cinder-tempest-plugin.git branch=master
ARG CINDER_TEMPEST_PLUGIN_GIT_REF=058e172729cde892e61ee65c931d5defc0d3d81c
ADD --keep-git-dir=true https://github.com/openstack/cinder-tempest-plugin.git#${CINDER_TEMPEST_PLUGIN_GIT_REF} /src/cinder-tempest-plugin
RUN git -C /src/cinder-tempest-plugin fetch --unshallow
# renovate: name=openstack/heat-tempest-plugin repo=https://github.com/openstack/heat-tempest-plugin.git branch=master
ARG HEAT_TEMPEST_PLUGIN_GIT_REF=f34d401bd2d89b07560c020e97d44e1bbe5236ce
ADD --keep-git-dir=true https://github.com/openstack/heat-tempest-plugin.git#${HEAT_TEMPEST_PLUGIN_GIT_REF} /src/heat-tempest-plugin
RUN git -C /src/heat-tempest-plugin fetch --unshallow
# renovate: name=openstack/keystone-tempest-plugin repo=https://github.com/openstack/keystone-tempest-plugin.git branch=master
ARG KEYSTONE_TEMPEST_PLUGIN_GIT_REF=97d6de342fc0b7487c2dc99765c4717850758afc
ADD --keep-git-dir=true https://github.com/openstack/keystone-tempest-plugin.git#${KEYSTONE_TEMPEST_PLUGIN_GIT_REF} /src/keystone-tempest-plugin
RUN git -C /src/keystone-tempest-plugin fetch --unshallow
# renovate: name=openstack/neutron-tempest-plugin repo=https://github.com/openstack/neutron-tempest-plugin.git branch=master
ARG NEUTRON_TEMPEST_PLUGIN_GIT_REF=27c0c5ba5abc21aa340e27a7d5e8981ab3249d33
ADD --keep-git-dir=true https://github.com/openstack/neutron-tempest-plugin.git#${NEUTRON_TEMPEST_PLUGIN_GIT_REF} /src/neutron-tempest-plugin
RUN git -C /src/neutron-tempest-plugin fetch --unshallow
# renovate: name=openstack/octavia-tempest-plugin repo=https://github.com/openstack/octavia-tempest-plugin.git branch=master
ARG OCTAVIA_TEMPEST_PLUGIN_GIT_REF=31ccc63c4f61c8f6a120cbe3f496da7c383c9a47
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
