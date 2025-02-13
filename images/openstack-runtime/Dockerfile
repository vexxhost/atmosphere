# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM base
RUN <<EOF bash -xe
apt-get update -qq
apt-get -o Dpkg::Options::="--force-confmiss" install --reinstall netbase
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
ONBUILD ARG PROJECT
ONBUILD ARG SHELL=/usr/sbin/nologin
ONBUILD RUN \
    groupadd -g 42424 ${PROJECT} && \
    useradd -u 42424 -g 42424 -M -d /var/lib/${PROJECT} -s ${SHELL} -c "${PROJECT} User" ${PROJECT} && \
    mkdir -p /etc/${PROJECT} /var/log/${PROJECT} /var/lib/${PROJECT} /var/cache/${PROJECT} && \
    chown -Rv ${PROJECT}:${PROJECT} /etc/${PROJECT} /var/log/${PROJECT} /var/lib/${PROJECT} /var/cache/${PROJECT}
