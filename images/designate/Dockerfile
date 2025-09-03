# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-26T17:38:39Z

FROM openstack-venv-builder AS build
# renovate: name=openstack/designate repo=https://opendev.org/openstack/designate.git branch=unmaintained/zed
ARG DESIGNATE_GIT_REF=f84acb20aba00eb5a584dcbb25e2abb5968bb427
ADD --keep-git-dir=true https://opendev.org/openstack/designate.git#${DESIGNATE_GIT_REF} /src/designate
RUN git -C /src/designate fetch --unshallow
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
