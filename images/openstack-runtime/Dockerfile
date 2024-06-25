# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-25T13:53:44Z

ARG RELEASE

ARG FROM=registry.atmosphere.dev/library/ubuntu-cloud-archive:${RELEASE}
FROM ${FROM}
ONBUILD ARG PROJECT
ONBUILD ARG SHELL=/usr/sbin/nologin
ONBUILD RUN \
    groupadd -g 42424 ${PROJECT} && \
    useradd -u 42424 -g 42424 -M -d /var/lib/${PROJECT} -s ${SHELL} -c "${PROJECT} User" ${PROJECT} && \
    mkdir -p /etc/${PROJECT} /var/log/${PROJECT} /var/lib/${PROJECT} /var/cache/${PROJECT} && \
    chown -Rv ${PROJECT}:${PROJECT} /etc/${PROJECT} /var/log/${PROJECT} /var/lib/${PROJECT} /var/cache/${PROJECT}
