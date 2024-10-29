# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-10-14T18:43:39Z

ARG RELEASE

FROM harbor.atmosphere.dev/library/ubuntu-cloud-archive:${RELEASE}
ENV PATH=/var/lib/openstack/bin:$PATH
RUN \
    apt-get update -qq && \
    apt-get install -qq -y --no-install-recommends \
        ca-certificates \
        libpcre3 \
        libpython3.10 \
        lsb-release \
        python3-setuptools \
        sudo && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
