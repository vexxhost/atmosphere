# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM ubuntu-cloud-archive
ENV PATH=/var/lib/openstack/bin:$PATH
RUN \
    apt-get update -qq && \
    apt-get install -qq -y --no-install-recommends \
        ca-certificates \
        libpython3.12 \
        lsb-release \
        libpcre3 \
        python3-setuptools \
        sudo && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
