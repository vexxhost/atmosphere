# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-26T17:38:39Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/octavia repo=https://opendev.org/openstack/octavia.git branch=stable/2024.1
ARG OCTAVIA_GIT_REF=7694a87a759fec8d9f9cc1cc3b86b71058a4324c
ADD --keep-git-dir=true https://opendev.org/openstack/octavia.git#${OCTAVIA_GIT_REF} /src/octavia
RUN git -C /src/octavia fetch --unshallow
# renovate: name=openstack/ovn-octavia-provider repo=https://opendev.org/openstack/ovn-octavia-provider.git branch=stable/2024.1
ARG OVN_OCTAVIA_PROVIDER_GIT_REF=5f0b2d89e8c2b3ddf8849c4d7e48325d9304afdc
ADD --keep-git-dir=true https://opendev.org/openstack/ovn-octavia-provider.git#${OVN_OCTAVIA_PROVIDER_GIT_REF} /src/ovn-octavia-provider
RUN git -C /src/ovn-octavia-provider fetch --unshallow
ARG REQUIREMENTS_GIT_REF=3a697f8e7a691db0c0a8cef883df130901338182
ADD --keep-git-dir=true https://opendev.org/openstack/requirements.git#${REQUIREMENTS_GIT_REF} /src/requirements2
RUN cp /src/requirements2/upper-constraints.txt /upper-constraints2.txt
RUN <<EOF sh -xe
sed -i '/glance-store/d' /upper-constraints2.txt
sed -i '/horizon/d' /upper-constraints2.txt
EOF
#RUN <<EOF bash -xe
#sed -i '/taskflow===.*/d' /upper-constraints.txt
#sed -i '/redis===.*/d' /upper-constraints.txt
#sed -i '/pyOpenSSL===.*/d' /upper-constraints.txt
#EOF
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints2.txt \
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
