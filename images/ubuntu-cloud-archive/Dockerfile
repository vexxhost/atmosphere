# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-10-14T18:43:39Z

ARG RELEASE

FROM harbor.atmosphere.dev/library/ubuntu:${RELEASE}
COPY trusted.gpg.d/ubuntu-cloud-keyring.gpg /etc/apt/trusted.gpg.d/ubuntu-cloud-keyring.gpg
COPY <<EOF /etc/apt/sources.list.d/cloudarchive.list
deb http://ubuntu-cloud.archive.canonical.com/ubuntu noble-updates/dalmatian main
EOF
