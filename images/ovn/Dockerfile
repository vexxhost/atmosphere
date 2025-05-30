# SPDX-FileCopyrightText: © 2025 VEXXHOST, Inc.
# SPDX-License-Identifier: GPL-3.0-or-later
# Atmosphere-Rebuild-Time: 2024-10-31T12:56:04Z

FROM golang AS ovn-kubernetes
ARG OVN_KUBERNETES_REF=5359e7d7f872058b6e5bf884c9f19d1922451f29
ADD https://github.com/ovn-kubernetes/ovn-kubernetes.git#${OVN_KUBERNETES_REF} /src
COPY patches/ovn-kubernetes /patches/ovn-kubernetes
RUN git -C /src apply --verbose /patches/ovn-kubernetes/*
RUN <<EOF bash -xe
cd /src/go-controller
go build -o /usr/bin/ovn-kube-util ./cmd/ovn-kube-util
EOF

FROM openvswitch
ENV OVS_USER_ID=42424
ARG TARGETPLATFORM
ADD --chmod=755 https://dl.k8s.io/release/v1.29.3/bin/${TARGETPLATFORM}/kubectl /usr/local/bin/kubectl
ARG OVN_SERIES=24.03
ARG OVN_VERSION=${OVN_SERIES}.2-34
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
COPY --from=ovsinit /usr/local/bin/ovsinit /usr/local/bin/ovsinit
RUN <<EOF bash -xe
    usermod -u 42424 openvswitch
    mkdir -p  /var/log/ovn /var/lib/ovn /var/run/ovn
    chown -Rv 42424:42424 /var/log/ovn /var/lib/ovn /var/run/ovn
EOF
