# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2025-02-20T21:42:46Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/designate repo=https://opendev.org/openstack/designate.git branch=stable/2024.2
ARG DESIGNATE_GIT_REF=5490df4e6b60f00e31e0ff57f863e406728e4eef
ADD --keep-git-dir=true https://opendev.org/openstack/designate.git#${DESIGNATE_GIT_REF} /src/designate
RUN git -C /src/designate fetch --unshallow
COPY patches/designate /patches/designate
RUN git -C /src/designate apply --verbose /patches/designate/*
RUN --mount=type=cache,target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        /src/designate
EOF

FROM openstack-python-runtime
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    bind9utils
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
