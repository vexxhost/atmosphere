# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-10-14T10:18:12Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/placement repo=https://github.com/openstack/placement.git branch=stable/2025.2
ARG PLACEMENT_GIT_REF=f9959dc2a58e30d6721f8e94bb86cbdef92fb26c
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
