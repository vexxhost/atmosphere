# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-05-30T20:29:01Z

ARG RELEASE

FROM registry.atmosphere.dev/library/openstack-runtime:${RELEASE}
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    openssh-server \
    openssh-client
EOF
RUN <<EOF bash -xe
chown -R nova: /etc/ssh
mkdir /var/run/sshd
chmod 0755 /var/run/sshd
EOF
