FROM ubuntu-cloud-archive
ARG TARGETARCH
ARG TARGETVARIANT
ARG RELEASE
RUN \
    --mount=type=cache,id=apt-$TARGETARCH$TARGETVARIANT-$RELEASE-var-cache-apt,sharing=locked,target=/var/cache/apt \
    --mount=type=cache,id=apt-$TARGETARCH$TARGETVARIANT-$RELEASE-var-lib-apt-lists,sharing=locked,target=/var/lib/apt/lists <<EOF bash -xe
apt-get update -qq
apt-get install -qq -y --no-install-recommends \
    ca-certificates \
    libpython3.10 \
    lsb-release \
    python3-distutils \
    sudo
EOF

ONBUILD ARG PROJECT
ONBUILD ARG SHELL=/usr/sbin/nologin
ONBUILD RUN \
    groupadd -g 42424 ${PROJECT} && \
    useradd -u 42424 -g 42424 -M -d /var/lib/${PROJECT} -s ${SHELL} -c "${PROJECT} User" ${PROJECT} && \
    mkdir -p /etc/${PROJECT} /var/log/${PROJECT} /var/lib/${PROJECT} /var/cache/${PROJECT} && \
    chown -Rv ${PROJECT}:${PROJECT} /etc/${PROJECT} /var/log/${PROJECT} /var/lib/${PROJECT} /var/cache/${PROJECT}
ONBUILD ENV PATH=/var/lib/openstack/bin:$PATH
