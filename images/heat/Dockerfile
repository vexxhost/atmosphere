# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-10-14T10:18:12Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/heat repo=https://github.com/openstack/heat.git branch=stable/2025.2
ARG HEAT_GIT_REF=c0eb453520be1b382d98cdd537adecaf8f9f48d9
ADD --keep-git-dir=true https://github.com/openstack/heat.git#${HEAT_GIT_REF} /src/heat
RUN git -C /src/heat fetch --unshallow
ARG UV_CACHE_ID=uv-default
RUN --mount=type=cache,id=${UV_CACHE_ID},target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        /src/heat
EOF

FROM openstack-python-runtime
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    curl jq
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
