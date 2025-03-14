# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-26T17:38:39Z

FROM ubuntu AS helm
ARG TARGETOS
ARG TARGETARCH
ARG HELM_VERSION=3.14.0
ADD https://get.helm.sh/helm-v${HELM_VERSION}-${TARGETOS}-${TARGETARCH}.tar.gz /helm.tar.gz
RUN tar -xzf /helm.tar.gz
RUN mv /${TARGETOS}-${TARGETARCH}/helm /usr/bin/helm

FROM openstack-venv-builder AS build
ARG MAGNUM_GIT_REF=2045ffb5ccbfb7873228eba9a6cecc1f65f4ab3f
ADD --keep-git-dir=true https://opendev.org/openstack/magnum.git#${MAGNUM_GIT_REF} /src/magnum
RUN git -C /src/magnum fetch --unshallow
COPY patches/magnum /patches/magnum
RUN git -C /src/magnum apply --verbose /patches/magnum/*
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
sed -i s/^oslo.db===.*$/oslo.db==14.1.0/ /upper-constraints.txt
pip3 install \
    --constraint /upper-constraints.txt \
        /src/magnum \
        magnum-cluster-api==0.29.0
EOF

FROM openstack-python-runtime
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    haproxy
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=helm --link /usr/bin/helm /usr/local/bin/helm
COPY --from=build --link /var/lib/openstack /var/lib/openstack
