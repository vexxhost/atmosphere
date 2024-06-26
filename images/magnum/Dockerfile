# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-26T11:52:25Z

ARG RELEASE

FROM registry.atmosphere.dev/library/ubuntu:${RELEASE} AS helm
ARG TARGETOS
ARG TARGETARCH
ARG HELM_VERSION=3.14.0
ADD https://get.helm.sh/helm-v${HELM_VERSION}-${TARGETOS}-${TARGETARCH}.tar.gz /helm.tar.gz
RUN tar -xzf /helm.tar.gz
RUN mv /${TARGETOS}-${TARGETARCH}/helm /usr/bin/helm

FROM registry.atmosphere.dev/library/openstack-venv-builder:${RELEASE} AS build
ARG MAGNUM_GIT_REF=2045ffb5ccbfb7873228eba9a6cecc1f65f4ab3f
ADD --keep-git-dir=true https://opendev.org/openstack/magnum.git#${MAGNUM_GIT_REF} /src/magnum
RUN git -C /src/magnum fetch --unshallow
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/magnum \
        magnum-cluster-api==0.19.2
EOF

FROM registry.atmosphere.dev/library/openstack-python-runtime:${RELEASE}
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    haproxy
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=helm --link /usr/bin/helm /usr/local/bin/helm
COPY --from=build --link /var/lib/openstack /var/lib/openstack
