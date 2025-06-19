# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-06-25T22:49:25Z

FROM ubuntu-cloud-archive AS requirements
# renovate: name=openstack/requirements repo=https://opendev.org/openstack/requirements.git branch=stable/2025.1
ARG REQUIREMENTS_GIT_REF=e31b331399de82c2277635b0c2ee2a6a271cd229
ADD --keep-git-dir=true https://opendev.org/openstack/requirements.git#${REQUIREMENTS_GIT_REF} /src/requirements
RUN cp /src/requirements/upper-constraints.txt /upper-constraints.txt
RUN <<EOF sh -xe
sed -i '/glance_store/d' /upper-constraints.txt
sed -i '/horizon/d' /upper-constraints.txt
EOF

FROM python-base
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
RUN --mount=type=cache,target=/root/.cache/uv <<EOF bash -xe
uv cache clean uwsgi
uv venv --system-site-packages /var/lib/openstack
uv pip install \
    --constraint /upper-constraints.txt \
        cryptography \
        pymysql \
        python-binary-memcached \
        python-memcached \
        uwsgi
EOF
