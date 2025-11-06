# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/manila repo=https://github.com/openstack/manila.git branch=master
ARG MANILA_GIT_REF=da85a864b83ef11a068c08f64e1955a45953dc03
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
    iproute2 openvswitch-switch
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
