# SPDX-License-Identifier: Apache-2.0
# Atmosphere-Rebuild-Time: 2024-06-25T13:53:44Z

ARG RELEASE

FROM golang:1.20 AS ovn-kubernetes
ARG OVN_KUBERNETES_REF=5359e7d7f872058b6e5bf884c9f19d1922451f29
ADD https://github.com/ovn-org/ovn-kubernetes.git#${OVN_KUBERNETES_REF} /src
COPY patches/ovn-kubernetes /patches/ovn-kubernetes
RUN git -C /src apply --verbose /patches/ovn-kubernetes/*
RUN <<EOF bash -xe
cd /src/go-controller
go build -o /usr/bin/ovn-kube-util ./cmd/ovn-kube-util
EOF

FROM registry.atmosphere.dev/library/openvswitch:${RELEASE}
ADD --chmod=755 https://dl.k8s.io/release/v1.29.3/bin/linux/amd64/kubectl /usr/local/bin/kubectl
ARG OVN_SERIES=23.09
ARG OVN_VERSION=${OVN_SERIES}.0-136
RUN <<EOF sh -xe
dnf -y --setopt=install_weak_deps=False --setopt=tsflags=nodocs install \
    firewalld-filesystem hostname ovn${OVN_SERIES}-${OVN_VERSION}.el9s procps-ng
dnf -y clean all
rm -rf /var/cache/dnf
EOF
ARG OVN_COMPONENT
RUN <<EOF sh -xe
dnf -y --setopt=install_weak_deps=False --setopt=tsflags=nodocs install \
    ovn${OVN_SERIES}-${OVN_COMPONENT}-${OVN_VERSION}.el9s
dnf -y clean all
rm -rf /var/cache/dnf
EOF
COPY --from=ovn-kubernetes --link /src/dist/images/ovndb-raft-functions.sh /root/ovndb-raft-functions.sh
COPY --from=ovn-kubernetes --link /src/dist/images/ovnkube.sh /root/ovnkube.sh
COPY --from=ovn-kubernetes --link /usr/bin/ovn-kube-util /usr/bin/ovn-kube-util
