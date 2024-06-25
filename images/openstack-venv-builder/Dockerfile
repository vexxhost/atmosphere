# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

# Build

ARG RELEASE

FROM registry.atmosphere.dev/library/ubuntu-cloud-archive:${RELEASE} AS requirements
ARG REQUIREMENTS_GIT_REF=c15ff09802a7cc4561275c9c0dbcfed9213c6e11
ADD --keep-git-dir=true https://opendev.org/openstack/requirements.git#${REQUIREMENTS_GIT_REF} /src/requirements
RUN cp /src/requirements/upper-constraints.txt /upper-constraints.txt
RUN <<EOF sh -xe
sed -i '/glance-store/d' /upper-constraints.txt
sed -i '/horizon/d' /upper-constraints.txt
EOF

FROM registry.atmosphere.dev/library/python-base:${RELEASE}
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    build-essential \
    git \
    libldap2-dev \
    libpcre3-dev \
    libsasl2-dev \
    libssl-dev \
    lsb-release \
    openssh-client \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
RUN python3 -m venv --upgrade-deps --system-site-packages /var/lib/openstack
COPY --from=requirements --link /upper-constraints.txt /upper-constraints.txt
RUN pip3 install \
    --constraint /upper-constraints.txt \
        cryptography \
        pymysql \
        python-binary-memcached \
        python-memcached \
        uwsgi
