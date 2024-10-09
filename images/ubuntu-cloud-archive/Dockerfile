# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-09-23T21:18:36Z

ARG RELEASE

FROM registry.atmosphere.dev/library/ubuntu:${RELEASE}
COPY trusted.gpg.d/ubuntu-cloud-keyring.gpg /etc/apt/trusted.gpg.d/ubuntu-cloud-keyring.gpg
COPY <<EOF /etc/apt/sources.list.d/cloudarchive.list
deb http://ubuntu-cloud.archive.canonical.com/ubuntu noble-updates/dalmatian main
EOF
