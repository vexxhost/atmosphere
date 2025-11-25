# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-10-14T10:18:12Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/manila repo=https://github.com/openstack/manila.git branch=stable/2025.2
ARG MANILA_GIT_REF=a4646de8740620b96d3b8ff8ff3ed7248cfb45dd
ADD --keep-git-dir=true https://github.com/openstack/manila.git#${MANILA_GIT_REF} /src/manila
RUN git -C /src/manila fetch --unshallow
ARG UV_CACHE_ID=uv-default
RUN --mount=type=cache,id=${UV_CACHE_ID},target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        /src/manila
EOF

FROM openstack-python-runtime
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    iproute2 openvswitch-switch python3-ceph-argparse python3-rados
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
