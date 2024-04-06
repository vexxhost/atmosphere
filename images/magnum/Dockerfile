# Copyright (c) 2024 VEXXHOST, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

FROM registry.atmosphere.dev/library/ubuntu:zed AS helm
ARG TARGETOS
ARG TARGETARCH
ARG HELM_VERSION=3.14.0
ADD https://get.helm.sh/helm-v${HELM_VERSION}-${TARGETOS}-${TARGETARCH}.tar.gz /helm.tar.gz
RUN tar -xzf /helm.tar.gz
RUN mv /${TARGETOS}-${TARGETARCH}/helm /usr/bin/helm

FROM registry.atmosphere.dev/library/openstack-venv-builder:zed AS build
ARG MAGNUM_GIT_REF=0ee979099a01ae2c8b1b5d6757897a8993e4e34c
ADD --keep-git-dir=true https://opendev.org/openstack/magnum.git#${MAGNUM_GIT_REF} /src/magnum
RUN git -C /src/magnum fetch --unshallow
COPY patches/magnum /patches/magnum
RUN git -C /src/magnum apply --verbose /patches/magnum/*
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip,sharing=private <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/magnum \
        magnum-cluster-api==0.16.0
EOF

FROM registry.atmosphere.dev/library/openstack-python-runtime:zed
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    haproxy
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=helm --link /usr/bin/helm /usr/local/bin/helm
COPY --from=build --link /var/lib/openstack /var/lib/openstack
