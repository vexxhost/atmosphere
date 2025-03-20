# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-26T17:38:39Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/octavia repo=https://opendev.org/openstack/octavia.git branch=unmaintained/2023.1
ARG OCTAVIA_GIT_REF=06251e9716719dd8f62144ecd41d26360a539f7d
ADD --keep-git-dir=true https://opendev.org/openstack/octavia.git#${OCTAVIA_GIT_REF} /src/octavia
RUN git -C /src/octavia fetch --unshallow
# renovate: name=openstack/ovn-octavia-provider repo=https://opendev.org/openstack/ovn-octavia-provider.git branch=unmaintained/2023.1
ARG OVN_OCTAVIA_PROVIDER_GIT_REF=393b8bd811f5cc63213286048efe6c5431151a0b
ADD --keep-git-dir=true https://opendev.org/openstack/ovn-octavia-provider.git#${OVN_OCTAVIA_PROVIDER_GIT_REF} /src/ovn-octavia-provider
RUN git -C /src/ovn-octavia-provider fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
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
