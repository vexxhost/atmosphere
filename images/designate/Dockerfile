# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/designate repo=https://github.com/openstack/designate.git branch=master
ARG DESIGNATE_GIT_REF=595894be2202bfd98805a0ed87281e69c59b5c1d
ADD --keep-git-dir=true https://github.com/openstack/designate.git#${DESIGNATE_GIT_REF} /src/designate
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
