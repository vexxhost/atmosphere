# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM openstack-runtime
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
