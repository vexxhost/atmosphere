# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM openstack-venv-builder AS build
ARG OCTAVIA_GIT_REPO
ARG OCTAVIA_GIT_REF
ADD --keep-git-dir=true ${OCTAVIA_GIT_REPO}#${OCTAVIA_GIT_REF} /src/octavia
RUN git -C /src/octavia fetch --unshallow
ARG OVN_OCTAVIA_PROVIDER_GIT_REPO
ARG OVN_OCTAVIA_PROVIDER_GIT_REF
ADD --keep-git-dir=true ${OVN_OCTAVIA_PROVIDER_GIT_REPO}#${OVN_OCTAVIA_PROVIDER_GIT_REF} /src/ovn-octavia-provider
RUN git -C /src/ovn-octavia-provider fetch --unshallow
RUN --mount=type=cache,target=/root/.cache/uv <<EOF bash -xe
uv pip install \
    --constraint /upper-constraints.txt \
        /src/octavia \
        /src/ovn-octavia-provider
EOF

FROM openstack-python-runtime
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    isc-dhcp-client openssh-client
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=build --link /var/lib/openstack /var/lib/openstack
