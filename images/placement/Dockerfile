# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM ghcr.io/vexxhost/openstack-venv-builder:main@sha256:bff09007027c2b6b908e2e970fe5cf06a4c025848e69bad73aa4970aff4978e2 AS build
# renovate: name=openstack/placement repo=https://github.com/openstack/placement.git branch=master
ARG PLACEMENT_GIT_REF=2df2316c370128ee3aaca2179b7a4b33d96f37ae
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
