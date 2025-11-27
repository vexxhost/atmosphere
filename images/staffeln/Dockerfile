# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM ghcr.io/vexxhost/openstack-venv-builder:main@sha256:bff09007027c2b6b908e2e970fe5cf06a4c025848e69bad73aa4970aff4978e2 AS build
ARG STAFFELN_GIT_REF=v2.2.3
ADD --keep-git-dir=true https://github.com/vexxhost/staffeln.git#${STAFFELN_GIT_REF} /src/staffeln
RUN git -C /src/staffeln fetch --unshallow
ARG UV_CACHE_ID=uv-default
RUN --mount=type=cache,id=${UV_CACHE_ID},target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        /src/staffeln
EOF

FROM ghcr.io/vexxhost/python-base:main@sha256:4ab6c0c1a31e169d3b158e8ad70963b91ea933ae63a279640ded5d37e92815b7
RUN \
    groupadd -g 42424 staffeln && \
    useradd -u 42424 -g 42424 -M -d /var/lib/staffeln -s /usr/sbin/nologin -c "Staffeln User" staffeln && \
    mkdir -p /etc/staffeln /var/log/staffeln /var/lib/staffeln /var/cache/staffeln && \
    chown -Rv staffeln:staffeln /etc/staffeln /var/log/staffeln /var/lib/staffeln /var/cache/staffeln
COPY --from=build --link /var/lib/openstack /var/lib/openstack
