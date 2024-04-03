FROM ubuntu:jammy-20240227 AS ubuntu
LABEL org.opencontainers.image.source=https://github.com/vexxhost/atmosphere

FROM ubuntu AS ubuntu-cloud-archive
ADD --chmod=644 https://git.launchpad.net/ubuntu/+source/ubuntu-keyring/plain/keyrings/ubuntu-cloud-keyring.gpg /etc/apt/trusted.gpg.d/ubuntu-cloud-keyring.gpg
ARG RELEASE
RUN <<EOF bash -xe
source /etc/os-release
if [ "\${VERSION_CODENAME}" = "jammy" ]; then \
    if [ "${RELEASE}" = "yoga" ]; then \
        # NOTE: Yoga shipped with 22.04, so no need to add an extra repository.
        echo "" > /etc/apt/sources.list.d/cloudarchive.list; \
    elif [ "${RELEASE}" = "zed" ]; then \
        echo "deb http://ubuntu-cloud.archive.canonical.com/ubuntu \${VERSION_CODENAME}-updates/${RELEASE} main" > /etc/apt/sources.list.d/cloudarchive.list; \
    elif [ "${RELEASE}" = "2023.1" ]; then \
        echo "deb http://ubuntu-cloud.archive.canonical.com/ubuntu \${VERSION_CODENAME}-updates/antelope main" > /etc/apt/sources.list.d/cloudarchive.list; \
    elif [ "${RELEASE}" = "2023.2" ]; then \
        echo "deb http://ubuntu-cloud.archive.canonical.com/ubuntu \${VERSION_CODENAME}-updates/bobcat main" > /etc/apt/sources.list.d/cloudarchive.list; \
    elif [ "${RELEASE}" = "master" ]; then \
        echo "deb http://ubuntu-cloud.archive.canonical.com/ubuntu \${VERSION_CODENAME}-updates/caracal main" > /etc/apt/sources.list.d/cloudarchive.list; \
    else \
        echo "${RELEASE} is not supported on \${VERSION_CODENAME}"; \
        exit 1; \
    fi; \
else
    echo "Unsupported release"; \
    exit 1; \
fi
EOF

FROM alpine/git AS requirements
ARG BRANCH
ADD https://opendev.org/openstack/requirements.git#${BRANCH} /src
RUN <<EOF sh -xe
sed -i 's/cryptography===36.0.2/cryptography===42.0.4/' /src/upper-constraints.txt
sed -i 's/cryptography===40.0.2/cryptography===42.0.4/' /src/upper-constraints.txt
sed -i 's/cryptography===41.0.7/cryptography===42.0.4/' /src/upper-constraints.txt
sed -i 's/Django===3.2.18/Django===3.2.24/' /src/upper-constraints.txt
sed -i 's/Flask===2.2.3/Flask===2.2.5/' /src/upper-constraints.txt
sed -i 's/Jinja2===3.1.2/Jinja2===3.1.3/' /src/upper-constraints.txt
sed -i 's/oauthlib===3.2.0/oauthlib===3.2.2/' /src/upper-constraints.txt
sed -i 's/paramiko===2.11.0/paramiko===3.4.0/' /src/upper-constraints.txt
sed -i 's/paramiko===3.1.0/paramiko===3.4.0/' /src/upper-constraints.txt
sed -i 's/protobuf===4.21.5/protobuf===4.21.6/' /src/upper-constraints.txt
sed -i 's/pyOpenSSL===22.0.0/pyOpenSSL===24.0.0/' /src/upper-constraints.txt
sed -i 's/pyOpenSSL===23.1.1/pyOpenSSL===24.0.0/' /src/upper-constraints.txt
sed -i 's/requests===2.28.1/requests===2.31.0/' /src/upper-constraints.txt
sed -i 's/requests===2.28.2/requests===2.31.0/' /src/upper-constraints.txt
sed -i 's/sqlparse===0.4.2/sqlparse===0.4.4/' /src/upper-constraints.txt
sed -i 's/urllib3===1.26.12/urllib3===1.26.18/' /src/upper-constraints.txt
sed -i 's/urllib3===1.26.15/urllib3===1.26.18/' /src/upper-constraints.txt
sed -i 's/Werkzeug===2.2.2/Werkzeug===2.3.8/' /src/upper-constraints.txt
sed -i 's/Werkzeug===2.2.3/Werkzeug===2.3.8/' /src/upper-constraints.txt
sed -i 's/zstd===1.5.2.5/zstd===1.5.4.0/' /src/upper-constraints.txt
sed -i '/glance-store/d' /src/upper-constraints.txt
sed -i '/horizon/d' /src/upper-constraints.txt
EOF

FROM ubuntu-cloud-archive AS openstack-venv-builder
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
EOF
RUN <<EOF bash -xe
python3 -m venv --upgrade-deps --system-site-packages /var/lib/openstack
EOF
ENV PATH=/var/lib/openstack/bin:$PATH
COPY --link --from=requirements /src/upper-constraints.txt /upper-constraints.txt
RUN <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        cryptography \
        pymysql \
        python-binary-memcached \
        python-memcached \
        uwsgi
EOF

FROM ubuntu-cloud-archive AS openstack-runtime
RUN <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    ca-certificates \
    libpython3.10 \
    lsb-release \
    python3-distutils \
    sudo
EOF
ARG PROJECT
ARG SHELL=/usr/sbin/nologin
RUN \
    groupadd -g 42424 ${PROJECT} && \
    useradd -u 42424 -g 42424 -M -d /var/lib/${PROJECT} -s ${SHELL} -c "${PROJECT} User" ${PROJECT} && \
    mkdir -p /etc/${PROJECT} /var/log/${PROJECT} /var/lib/${PROJECT} /var/cache/${PROJECT} && \
    chown -Rv ${PROJECT}:${PROJECT} /etc/${PROJECT} /var/log/${PROJECT} /var/lib/${PROJECT} /var/cache/${PROJECT}
ENV PATH=/var/lib/openstack/bin:$PATH

FROM alpine/git AS barbican-src
ARG BARBICAN_GIT_REF
ADD --keep-git-dir=true https://opendev.org/openstack/barbican.git#${BARBICAN_GIT_REF} /src
RUN git -C /src fetch --unshallow

FROM openstack-venv-builder AS barbican-build
COPY --from=barbican-src --link /src /src/barbican
RUN <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        /src/barbican \
        pykmip
EOF

FROM openstack-runtime AS barbican
COPY --from=barbican-build --link /var/lib/openstack /var/lib/openstack
