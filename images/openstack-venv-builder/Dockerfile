# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-05-30T20:29:01Z

ARG RELEASE

FROM registry.atmosphere.dev/library/ubuntu-cloud-archive:${RELEASE} AS requirements
ADD https://releases.openstack.org/constraints/upper/zed /upper-constraints.txt
RUN <<EOF sh -xe
sed -i 's/cryptography===36.0.2/cryptography===42.0.4/' /upper-constraints.txt
sed -i 's/Django===3.2.15/Django===3.2.24/' /upper-constraints.txt
sed -i 's/Flask===2.2.2/Flask===2.2.5/' /upper-constraints.txt
sed -i 's/Jinja2===3.1.2/Jinja2===3.1.3/' /upper-constraints.txt
sed -i 's/oauthlib===3.2.0/oauthlib===3.2.2/' /upper-constraints.txt
sed -i 's/paramiko===2.11.0/paramiko===3.4.0/' /upper-constraints.txt
sed -i 's/protobuf===4.21.5/protobuf===4.21.6/' /upper-constraints.txt
sed -i 's/pyOpenSSL===22.0.0/pyOpenSSL===24.0.0/' /upper-constraints.txt
sed -i 's/requests===2.28.1/requests===2.31.0/' /upper-constraints.txt
sed -i 's/sqlparse===0.4.2/sqlparse===0.4.4/' /upper-constraints.txt
sed -i 's/urllib3===1.26.12/urllib3===1.26.18/' /upper-constraints.txt
sed -i 's/Werkzeug===2.2.2/Werkzeug===2.3.8/' /upper-constraints.txt
sed -i 's/zstd===1.5.2.5/zstd===1.5.4.0/' /upper-constraints.txt
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
