# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-02-20T21:42:46Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/heat repo=https://opendev.org/openstack/heat.git branch=stable/2024.2
ARG HEAT_GIT_REF=64bdbb9bc66c38760989dd7bb2574ccc14069872
ADD --keep-git-dir=true https://opendev.org/openstack/heat.git#${HEAT_GIT_REF} /src/heat
RUN git -C /src/heat fetch --unshallow
RUN --mount=type=cache,target=/root/.cache/uv <<EOF bash -xe
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
