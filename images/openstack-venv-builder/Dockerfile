# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM ghcr.io/vexxhost/ubuntu-cloud-archive:2025.2@sha256:393e3d9c51fe69efb34cf629d2c9c1c80613b5f09d5c9919a2d959c0a84ab5ec AS requirements
# renovate: name=openstack/requirements repo=https://github.com/openstack/requirements.git branch=master
ARG REQUIREMENTS_GIT_REF=d953bdbff8c1357447e53e4230e88949745fa395
ADD --keep-git-dir=true https://github.com/openstack/requirements.git#${REQUIREMENTS_GIT_REF} /src/requirements
RUN cp /src/requirements/upper-constraints.txt /upper-constraints.txt
RUN <<EOF sh -xe
sed -i '/glance_store/d' /upper-constraints.txt
sed -i '/horizon/d' /upper-constraints.txt
EOF

FROM ghcr.io/vexxhost/python-base:main@sha256:4ab6c0c1a31e169d3b158e8ad70963b91ea933ae63a279640ded5d37e92815b7
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
    python3-dev
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=requirements --link /upper-constraints.txt /upper-constraints.txt
ARG UV_CACHE_ID=uv-default
RUN --mount=type=cache,id=${UV_CACHE_ID},target=/root/.cache/uv <<EOF bash -xe
uv venv --system-site-packages /var/lib/openstack
uv pip install \
    --constraint /upper-constraints.txt \
        confluent-kafka \
        cryptography \
        pymysql \
        python-binary-memcached \
        python-memcached \
        uwsgi
EOF
