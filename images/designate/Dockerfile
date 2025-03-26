# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-26T17:38:39Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/designate repo=https://opendev.org/openstack/designate.git branch=stable/2024.1
ARG DESIGNATE_GIT_REF=b905f44d6001ba9382fc5964d128007cb819b1ed
ADD --keep-git-dir=true https://opendev.org/openstack/designate.git#${DESIGNATE_GIT_REF} /src/designate
RUN git -C /src/designate fetch --unshallow
COPY patches/designate /patches/designate
RUN git -C /src/designate apply --verbose /patches/designate/*
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
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
