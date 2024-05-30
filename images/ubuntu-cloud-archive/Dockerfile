# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-05-30T20:29:01Z

ARG RELEASE

FROM registry.atmosphere.dev/library/ubuntu:${RELEASE}
COPY trusted.gpg.d/ubuntu-cloud-keyring.gpg /etc/apt/trusted.gpg.d/ubuntu-cloud-keyring.gpg
COPY <<EOF /etc/apt/sources.list.d/cloudarchive.list
deb http://ubuntu-cloud.archive.canonical.com/ubuntu jammy-updates/caracal main
EOF
