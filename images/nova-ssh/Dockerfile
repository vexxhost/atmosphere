# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM ghcr.io/vexxhost/ubuntu-cloud-archive:2025.2@sha256:393e3d9c51fe69efb34cf629d2c9c1c80613b5f09d5c9919a2d959c0a84ab5ec
RUN <<EOF bash -xe
groupadd -g 42424 nova
useradd -u 42424 -g 42424 -M -d /var/lib/nova -s /bin/bash -c "nova User" nova
mkdir -p /etc/nova /var/log/nova /var/lib/nova /var/cache/nova
chown -Rv nova:nova /etc/nova /var/log/nova /var/lib/nova /var/cache/nova
EOF
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    iproute2 \
    openssh-server \
    openssh-client
EOF
RUN <<EOF bash -xe
chown -R nova: /etc/ssh
mkdir /var/run/sshd
chmod 0755 /var/run/sshd
EOF
COPY <<EOF /etc/ssh/sshd_config.d/00-hardening.conf
Ciphers aes256-ctr,aes192-ctr
MACs hmac-sha2-512,hmac-sha2-256
KexAlgorithms diffie-hellman-group-exchange-sha256
HostKeyAlgorithms ecdsa-sha2-nistp256,ecdsa-sha2-nistp384,ecdsa-sha2-nistp521
MaxAuthTries 3
EOF
