# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-26T17:38:39Z

FROM openstack-venv-builder AS build
ADD --keep-git-dir=true https://github.com/openstack/octavia.git#2023.2-eol /src/octavia
RUN git -C /src/octavia fetch --unshallow
COPY patches/octavia /patches/octavia
RUN git -C /src/octavia apply --verbose /patches/octavia/*
ADD --keep-git-dir=true https://github.com/openstack/ovn-octavia-provider.git#2023.2-eol /src/ovn-octavia-provider
RUN git -C /src/ovn-octavia-provider fetch --unshallow
RUN <<EOF bash -xe
 sed -i 's/taskflow===.*/taskflow===5.5.0/g' /upper-constraints.txt
EOF
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/octavia[redis] \
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
