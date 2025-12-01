# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/placement repo=https://github.com/openstack/placement.git branch=master
ARG PLACEMENT_GIT_REF=1c16485a11946441b0e4893ed9ee1cafadbe4527
ADD --keep-git-dir=true https://github.com/openstack/placement.git#${PLACEMENT_GIT_REF} /src/placement
RUN git -C /src/placement fetch --unshallow
ARG UV_CACHE_ID=uv-default
RUN --mount=type=cache,id=${UV_CACHE_ID},target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        /src/placement
EOF

FROM openstack-python-runtime
COPY --from=build --link /var/lib/openstack /var/lib/openstack
