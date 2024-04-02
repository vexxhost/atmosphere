FROM ubuntu-cloud-archive
ARG TARGETARCH
ARG TARGETVARIANT
ARG RELEASE
RUN \
    --mount=type=cache,id=apt-$TARGETARCH$TARGETVARIANT-$RELEASE-var-cache-apt,sharing=locked,target=/var/cache/apt \
    --mount=type=cache,id=apt-$TARGETARCH$TARGETVARIANT-$RELEASE-var-lib-apt-lists,sharing=locked,target=/var/lib/apt/lists <<EOF bash -xe
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
RUN \
    --mount=type=cache,id=pip-$TARGETARCH$TARGETVARIANT-$RELEASE-cache,sharing=locked,target=/root/.cache/pip <<EOF bash -xe
python3 -m venv --upgrade-deps --system-site-packages /var/lib/openstack
EOF
ENV PATH=/var/lib/openstack/bin:$PATH
COPY --link --from=requirements /src/upper-constraints.txt /upper-constraints.txt
RUN \
    --mount=type=cache,id=pip-$TARGETARCH$TARGETVARIANT-$RELEASE-cache,sharing=locked,target=/root/.cache/pip <<EOF bash -xe
pip3 install \
    --constraint /upper-constraints.txt \
        cryptography \
        pymysql \
        python-binary-memcached \
        python-memcached \
        uwsgi
EOF
